import requests

from ..material import Material, CzaCatalyst
from ..kinetic_models import KineticModel, co2_to_c1


class MaterialSeries:
    def __init__(self):
        self.materials: list[Material | CzaCatalyst] = []

    @property
    def kinetic_model_class(self) -> type[KineticModel | co2_to_c1.PowerLawCzaSim]:
        try:
            return self.materials[0].KINETIC_MODEL_CLASS
        except IndexError:
            raise AttributeError("Material series does not yet have any materials.")

    def upload_to_emp(self, host: str):
        material_list = [material.to_dict() for material in self.materials]
        url = host + "/api/upload_materials"
        return requests.post(url, json=material_list)

    # @property
    # def kinetic_model_class(self) -> type[KineticModel | co2_to_c1.PowerLawCzaSim]:
    #     try:
    #         return self.materials[0].KINETIC_MODEL_CLASS
    #     except IndexError:
    #         raise AttributeError(
    #             "Material series does not yet have any catalysts assigned."
    #         )
