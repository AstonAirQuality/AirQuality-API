from example import add


class Plume:
    def __init__(self, plume_id, plume_name, num1, num2):
        self.plume_id = plume_id
        self.plume_name = plume_name
        self.plume_description = add(num1, num2)

    def __str__(self):
        return f"Plume ID: {self.plume_id}, Plume Name: {self.plume_name}, Plume Description: {self.plume_description}"
