import requests
from typing import Any

from .expt import Expt
from .unit import Unit
from .. import quantities as quant
from ..utils import Time


class ExptSeries:
    def __init__(self, unit: Unit):
        self.expts: list[Expt] = []
        self.unit = unit
        last_expt_end = unit.last_expt_end()
        if last_expt_end is None:
            # self.start = Time(ET_str="1970-01-01_0000")
            self.start = Time(UET=0)
        else:
            self.start = last_expt_end + quant.TimeDelta(hr=1)

    def next_expt_start(self) -> Time:
        try:
            return self.expts[-1].steps[-1].end + quant.TimeDelta(hr=1)
        except IndexError:
            return self.start

    def upload_time_series_data_to_influx(self):
        # return [expt.upload_time_series_data_to_influx() for expt in self.expts]
        for expt in self.expts:
            print()
            print(f"Experiment {expt.series_id} of {len(self.expts)}:")
            print(expt.upload_time_series_data_to_influx())
            print()

    def upload_to_emp(self) -> dict[str, Any]:
        endpoint = f"/api/upload_expts"
        url = self.unit.host + endpoint
        expts_list = [expt.to_dict() for expt in self.expts]
        resp = requests.post(url, json=expts_list, timeout=10)

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
