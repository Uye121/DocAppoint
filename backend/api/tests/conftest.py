from pytest_factoryboy import register

from .factories import (
    UserFactory, PatientFactory, HealthcareProviderFactory,
    HospitalFactory, SpecialityFactory, AdminStaffFactory, SystemAdminFactory
)

for factory in (
    UserFactory, PatientFactory, HealthcareProviderFactory,
    HospitalFactory, SpecialityFactory, AdminStaffFactory, SystemAdminFactory
):
    register(factory)

# @pytest.fixture(scope="function", autouse=True)
# def memory_tracker(request):
#     """Track memory usage for each test."""
#     process = psutil.Process(os.getpid())
    
#     # Force garbage collection before test
#     gc.collect()
#     mem_before = process.memory_info().rss / 1024 / 1024  # MB
    
#     print(f"\n{'='*60}")
#     print(f"Test: {request.node.name}")
#     print(f"Memory before: {mem_before:.2f} MB")
    
#     yield
    
#     # Force garbage collection after test
#     gc.collect()
#     mem_after = process.memory_info().rss / 1024 / 1024  # MB
#     diff = mem_after - mem_before
    
#     print(f"Memory after: {mem_after:.2f} MB")
#     print(f"Memory diff: {diff:+.2f} MB")
    
#     if diff > 10:  # Alert for large increases
#         print(f"⚠️  LARGE MEMORY INCREASE: {diff:.2f} MB")
    
#     print(f"{'='*60}")