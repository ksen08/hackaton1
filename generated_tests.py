```python
import pytest
import allure
import requests

@allure.feature("Virtual Machines")
class TestVMOperations:
    @allure.title("Get VM by ID")
    def test_get_vm_by_id(self):
        # Arrange
        vm_id = "test-vm-id"
        vm_url = f"/vms/{vm_id}"

        # Act
        response = requests.get(vm_url)

        # Assert
        assert response.status_code == 200
        assert response.json()["name"] == "test-vm"

    @allure.title("Delete VM by ID")
    def test_delete_vm_by_id(self):
        # Arrange
        vm_id = "test-vm-id"
        vm_url = f"/vms/{vm_id}"

        # Act
        response = requests.delete(vm_url)

        # Assert
        assert response.status_code == 204
```