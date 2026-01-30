from itom_library import OOClient

client = OOClient(
    base_url='https://localhost:5555/oo',
    username='admin',
    password='Automation_1234',
    verify_ssl=False,
    table=True
)

flows = client.get_flows()
print(f"Retrieved {len(flows)} flows from the OO server.")
print(flows)

# inputs = client.get_flow_inputs("06fe8531-868b-4e79-aa7a-13a5e30a66ec")
# print(inputs)