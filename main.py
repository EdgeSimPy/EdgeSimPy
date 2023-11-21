from edge_sim_py import *

# Creating a simulator object
simulator = Simulator()

# Load existing dataset file from external JSON file from EdgeSimpy
simulator.initialize(input_file="datasets/sample_dataset1.json")

# Test to see if we can see some data with a basical for loop
for user in User.all():
    print(f"{user}. Coordinates: {user.coordinates}")
    
# Testing to see other objects from the dataset
for edge_server in EdgeServer.all():
    print(f"{edge_server}. CPU: {edge_server.cpu} cores")