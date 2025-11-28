import copy

from agents.matmaster_agent.constant import CURRENT_ENV, BohriumExecutor, BohriumStorge
from agents.matmaster_agent.sub_agents.mapping import (
    AGENT_IMAGE_ADDRESS,
    AGENT_MACHINE_TYPE,
)

DPACalulator_AGENT_NAME = 'dpa_calculator_agent'
if CURRENT_ENV in ['test', 'uat']:
    DPAMCPServerUrl = 'http://qpus1389933.bohrium.tech:50001/sse'
else:
    DPAMCPServerUrl = 'http://pfmx1355864.bohrium.tech:50001/sse'
    # DPAMCPServerUrl = 'https://dpa-uuid1750659890.app-space.dplink.cc/sse?token=7c2e8de61ec94f4e80ebcef1ac17c92e'
DPACalulator_BOHRIUM_EXECUTOR = copy.deepcopy(BohriumExecutor)
DPACalulator_BOHRIUM_EXECUTOR['machine']['remote_profile']['image_address'] = (
    AGENT_IMAGE_ADDRESS.get(DPACalulator_AGENT_NAME, '')
)
DPACalulator_BOHRIUM_EXECUTOR['machine']['remote_profile']['machine_type'] = (
    AGENT_MACHINE_TYPE.get(DPACalulator_AGENT_NAME) or 'c2_m4_cpu'
)
DPACalulator_BOHRIUM_STORAGE = copy.deepcopy(BohriumStorge)
