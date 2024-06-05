import gzip
import csv
import xml.dom.minidom
import pandas as pd
import zipfile
import shutil

with gzip.open('pubmed24n1219.xml.gz', 'rb') as fin:
    with open('myfile.xml', 'wb') as fout:
        shutil.copyfileobj(fin, fout)
        frame = pd.read_xml('myfile.xml')
        


