# import os

# from fhir_kindling.benchmark.bench import ServerBenchmark
# from fhir_kindling.fhir_server.fhir_server import FhirServer


# def test_benchmark():
#     server_1 = FhirServer(api_address=os.getenv("FHIR_API_URL"))
#     server_2 = FhirServer(api_address=os.getenv("TRANSFER_SERVER_URL"))
#     benchmark = ServerBenchmark(servers=[server_1, server_2], n_attempts=2, dataset_size=10)
#     benchmark.run_suite(progress=False)

#     assert True
