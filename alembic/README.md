Alembic – versjonshåndtering av databasen
==========================================

Kjør alle kommandoer under fra `midda_0.1/` (der `alembic.ini` ligger).
`env.py` henter `DATABASE_URL` fra `app/database.py` (sqlite-fil `midda_0.1/midda.db`
som default, med mindre `DATABASE_URL` er satt i miljøet/.env).


1) Opprette en helt ny database med versjonskontroll
-----------------------------------------------------

Når det ikke finnes noen `midda.db` og `alembic/versions/` er tom:

    cd midda_0.1

    # Generer en migrasjon ut fra modellene i app/models.py
    alembic revision --autogenerate -m "initial schema"

    # Les gjennom den genererte filen i alembic/versions/ FØR du kjører den,
    # og bekreft at upgrade()/downgrade() faktisk matcher modellene dine.

    # Kjør migrasjonen -> oppretter midda.db + tabeller + alembic_version
    alembic upgrade head

    # Verifiser
    alembic current
    sqlite3 midda.db ".tables"

`alembic upgrade head` er eneste måte databasen skal opprettes/oppdateres på i
dette prosjektet – ikke lag skript som kaller `Base.metadata.create_all()`
direkte, da mister Alembic oversikten over hvilken versjon databasen er på.


2) Legge til en ny kolonne
----------------------------

    # 1. Legg til det nye feltet i riktig modell i app/models.py, f.eks.:
    #    note: Mapped[str | None] = mapped_column(String(120))

    cd midda_0.1

    # 2. Generer migrasjon ut fra diffen mellom modellene og gjeldende db
    alembic revision --autogenerate -m "add note to dish_ingredients"

    # 3. Les gjennom filen i alembic/versions/ – autogenerate bommer ofte på
    #    server_default, nullability på eksisterende rader, og enum-endringer
    #    (se punkt 3). Rett opp manuelt ved behov.

    # 4. Kjør migrasjonen
    alembic upgrade head

    # Angre siste migrasjon om noe er galt
    alembic downgrade -1


3) Manuell enum-migrasjon med batch_alter_table (Unit-enumen)
----------------------------------------------------------------

Alembic sin `--autogenerate` sammenligner IKKE medlemmene i et Python-enum mot
CHECK-constrainten i databasen – en endring i `Unit`-enumen i `app/models.py`
blir aldri fanget opp automatisk. Denne migrasjonen må skrives for hånd.

Viktig detalj: SQLAlchemy sin `Enum`-type lagrer som standard `.name` på
medlemmene, ikke `.value`. For

    class Unit(enum.Enum):
        G = "g"
        KG = "kg"
        ML = "ml"
        DL = "dl"
        L = "l"
        TS = "ts"
        SS = "ss"
        STK = "stk"
        KLYPE = "klype"

er verdiene som faktisk ligger i databasens CHECK-constraint altså
`"G", "KG", "ML", "DL", "L", "TS", "SS", "STK", "KLYPE"` – ikke de små
bokstavene. Bruk `.name`-formen i migrasjonen.

SQLite støtter ikke å endre en CHECK-constraint med vanlig `ALTER TABLE`, så
Alembic må kjøre i batch-modus (den kopierer tabellen til en midlertidig
tabell med nytt skjema, kopierer dataene over, og bytter navn tilbake).

Eksempel: legge til et nytt medlem `SPSK = "spsk"` i `Unit`.

    cd midda_0.1

    # Opprett en TOM migrasjon – IKKE --autogenerate, den finner ikke dette selv
    alembic revision -m "add SPSK to unit enum"

Rediger den genererte filen i `alembic/versions/` slik:

    from alembic import op
    import sqlalchemy as sa

    # revision identifiers, brukes av Alembic.
    revision = "..."
    down_revision = "..."

    old_values = ("G", "KG", "ML", "DL", "L", "TS", "SS", "STK", "KLYPE")
    new_values = old_values + ("SPSK",)

    old_enum = sa.Enum(*old_values, name="unit")
    new_enum = sa.Enum(*new_values, name="unit")


    def upgrade() -> None:
        with op.batch_alter_table("dish_ingredients") as batch_op:
            batch_op.alter_column(
                "unit",
                existing_type=old_enum,
                type_=new_enum,
                existing_nullable=False,
            )


    def downgrade() -> None:
        # NB: nedgradering feiler hvis noen rader allerede bruker "SPSK" –
        # de må migreres/fjernes før du kan gå tilbake til old_enum.
        with op.batch_alter_table("dish_ingredients") as batch_op:
            batch_op.alter_column(
                "unit",
                existing_type=new_enum,
                type_=old_enum,
                existing_nullable=False,
            )

Deretter:

    alembic upgrade head
    alembic current

Samme mønster (batch_alter_table med old_enum/new_enum) brukes om du fjerner
eller endrer navn på et medlem – bytt bare ut hva `new_values` inneholder, og
husk at fjerning/renaming krever en egen `UPDATE`-setning inni `upgrade()` for
å migrere eksisterende rader til en gyldig verdi før constrainten strammes
inn (ellers feiler batch-kopieringen på rader med den gamle verdien).
