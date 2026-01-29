import os, requests, pandas as pd
from typing import List, Any, Optional

from .. import utils
from .. import quantities as quant
from .step import Step
from ..reactors import PFR
from .unit import Unit
from ..material import Material, Catalyst, CzaCatalyst
from ..kinetic_models import KineticModel, co2_to_c1


class Expt:
    steps: list[Step]

    @property
    def steady_state_steps(self) -> list[Step]:
        return [step for step in self.steps if step.step_name == "steadyState"]

    @property
    def date_str(self):
        return self.start.date_str

    def __init__(
        self,
        expt_class_name: str,
        reactor_class: type[PFR],
        step_class: type[Step],
        catalyst: Catalyst | CzaCatalyst,
        sample_mass: quant.Mass,
        unit: Unit,
        project_id: str,
        start: utils.Time,
        series_id: int,
        emp_dt_sec=180,
        notes: Optional[str] = None,
    ):
        self.expt_class_name = expt_class_name
        self.step_class = step_class
        self.reactor_class = reactor_class
        self.catalyst = catalyst
        self.sample_mass = sample_mass
        self.unit = unit
        self.project_id = project_id
        self.start = start
        self.series_id = series_id
        self.emp_dt_sec = emp_dt_sec
        self.notes = notes
        self.steps: list[Step] = []

    def add_step(
        self,
        step_name: str,
        duration: quant.TimeDelta,
        T: quant.Temperature,
        p0: quant.Pressure,
        whsv: Optional[quant.WHSV] = None,
        F0: Optional[quant.MolarFlowRate] = None,
        start: Optional[utils.Time] = None,
    ):
        if start is None:
            start = self.steps[-1].end
        end = start + duration
        reactor = self.reactor_class(
            T=T,
            kinetic_model=self.catalyst.get_kinetic_model(T=T),
            p0=p0,
            whsv=whsv,
            F0=F0,
            mcat=self.sample_mass,
            catalyst=self.catalyst,
        )
        step = self.step_class(
            self, step_name, len(self.steps) + 1, start, end, reactor
        )
        self.steps.append(step)

    def simulate(self, influx_dt_sec=60, std_dev: Optional[dict[str, float]] = None):
        for step in self.steps:
            step.simulate(influx_dt_sec, std_dev)
        dataframes = [step.time_series_data for step in self.steps]
        self.time_series_data = pd.concat(dataframes, ignore_index=True)
        self._compute_tos()
        for index, step in enumerate(self.steady_state_steps):
            step.steady_state_step_num = index + 1
        # self.molar_flow_rate_df = self.get_molar_flow_rates()
        self.step_summary_df = pd.DataFrame(
            [step.to_dict() for step in self.steady_state_steps]
        )

    def upload_time_series_data_to_influx(self) -> dict:
        self.unit.populate_attributes_from_emp()
        influx = utils.Influx(
            url=os.getenv("INFLUXDB_URL"),
            org=self.unit.org,
            bucket=self.unit.bucket,
            measurement=self.unit.measurement,
        )
        tag_map = {key: value["tag"] for key, value in self.unit.tags.items()}
        cols_to_upload = list(set(tag_map.keys()) & set(self.time_series_data.columns))
        cols_to_upload.append("timestamp")
        df = self.time_series_data[cols_to_upload]
        df = df.rename(columns=tag_map)
        return influx.upload_dataframe(dataframe=df, token=os.getenv("INFLUXDB_TOKEN"))

    def _compute_tos(self):
        for step in self.steps:
            if step.step_name == "steadyState":
                start = step.start.UET
                break
        tos_sec = self.time_series_data["timestamp"] - start
        self.time_series_data["tos_hr"] = tos_sec / 3600.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "expt_class_name": self.expt_class_name,
            "project_id": self.project_id,
            "unit_name": self.unit.unit_class_name,
            "prop__material__common_name": self.catalyst.common_name,
            "sample_mass_g": self.sample_mass.g,
            "prop__start__ET_str": self.steps[0].start.ET_str,
            "prop__end__ET_str": self.steps[-1].end.ET_str,
            "dt_sec": self.emp_dt_sec,
            "notes": self.notes,
        }

    def upload_to_emp(self, host: str, dt_sec=15) -> dict[str, Any]:
        endpoint = f"/api/upload_expt"
        url = host + endpoint
        # self.delete_from_emp(host)
        resp = requests.post(url, json=self.to_dict(), timeout=10)

        if not resp.ok:
            try:
                error_data = resp.json()
                return {"status_code": resp.status_code, "error": error_data}
            except ValueError:
                return {"status_code": resp.status_code, "body": resp.text}

        try:
            return resp.json()
        except ValueError:
            return {"status_code": resp.status_code, "body": resp.text}

    def delete_from_emp(self, host: str):
        endpoint = f"/api/delete_expt/{self.project_id}"
        if not host.startswith("http://") and not host.startswith("https://"):
            host = "http://" + host
        url = host + endpoint
        params = {"lab_notebook_id": self.lab_notebook_id, "project": self.project_id}
        resp = requests.delete(url, json=params, timeout=10)

        if not resp.ok:
            try:
                error_data = resp.json()
                return {"status_code": resp.status_code, "error": error_data}
            except ValueError:
                return {"status_code": resp.status_code, "body": resp.text}

        try:
            return resp.json()
        except ValueError:
            return {"status_code": resp.status_code, "body": resp.text}

    def compute_inlet_partial_pressures(self) -> pd.DataFrame:
        df = self.time_series_data.copy()
        mask = [col for col in df.columns if "_mfc_smLmin" in col]
        total_inlet_flow_molh = df[mask].sum(axis=1)
        for col in mask:
            y = df[col] / total_inlet_flow_molh
            p_col_id = f"p_{col.split('_mfc')[0]}_bar"
            df[p_col_id] = y * df["pressure"]
        return df
