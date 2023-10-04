from cyberwatch_api import Cyberwatch_Pyhelper

output = Cyberwatch_Pyhelper().request(
    method="get",
    endpoint="/api/v3/assets/servers/{id}",
    params={'id' : 1082}
)

for res in output :
    print(res.json())
