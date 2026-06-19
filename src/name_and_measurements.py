class NameAndMeasurements:
    def __init__(self, ingredient, measurement):
        self.name = ingredient
        self.measurement = measurement

    def __repr__(self):
        return f'NameAndMeasurements("{self.name}", "{self.measurement}")'