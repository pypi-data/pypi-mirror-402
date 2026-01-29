import ndex2
import networkx as nx
import pandas as pd
from data_import_tools import load_network_file
import sys
from getpass import getpass
import ndex2.client

if __name__ == "__main__":
    network="/cellar/users/snwright/Data/Network_Analysis/Processed_Data/v2_2022/v2_composite_min2_net.txt"
    G = load_network_file(network, id_type="Entrez", keep_attributes=True)
    print("Network loaded.")
    cx = ndex2.create_nice_cx_from_networkx(G)
    print("Network Converted.")
    my_account = "snwright"
    my_password = ""
    #my_account=getpass("Username")
    #my_password=getpass("Password")
    my_ndex=ndex2.client.Ndex2("http://public.ndexbio.org", my_account, my_password)
    cx.upload_to(client=my_ndex)
    print("Network Uploaded")
