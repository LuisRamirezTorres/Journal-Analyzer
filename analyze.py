import gzip
import shutil
import xml.etree.ElementTree as ET
import csv
import re

# Function used to excract .gz file and copy over to .xml file to be able to parse data
def extractGzipToXml(gzip_file, xmlFile):
    with gzip.open(gzip_file, 'rb') as fin:
        with open(xmlFile, 'wb') as fout:
            shutil.copyfileobj(fin, fout)

# Function used to parse the PubMedArticles
def parsePubMedArticles(xmlFile):
    # Parse xml file using ElementTree library
    tree = ET.parse(xmlFile)
    root = tree.getroot()

    
    
    journalsData = {}  


    # For every article found in the xml file, collect the data we want
    for article in root.findall('PubmedArticle'):
        pmid = article.findtext('MedlineCitation/PMID')                                                     #PMID
        pubDateYear = article.findtext('MedlineCitation/Article/Journal/JournalIssue/PubDate/Year')         #PubDate (Year)
        journalTitle = article.findtext('MedlineCitation/Article/Journal/Title')                            #Journal Title
        journalIso = article.findtext('MedlineCitation/Article/Journal/ISOAbbreviation')                    #ISO
        articleTitle = article.findtext('MedlineCitation/Article/ArticleTitle')                             #Article Title
        pagination = article.findtext('MedlineCitation/Article/Pagination/MedlinePgn')                      #Pagination
        abstract = article.findtext('MedlineCitation/Article/Abstract/AbstractText')                        #Abstract


        #Concatenate all abstract sections
        abstract = ""
        abstractSections = article.findall('MedlineCitation/Article/Abstract/AbstractText')
        for section in abstractSections:
            abstract += (section.text or "") + " "
        abstract = abstract.strip()



        #Create list for author forenames and affilations
        authorForeNames = []
        authorAffiliations = []

        #For every author found in the articles, collect forenames and affiliations
        for author in article.findall('MedlineCitation/Article/AuthorList/Author'):
            foreName = author.findtext('ForeName')
            affiliation = author.findtext('AffiliationInfo/Affiliation')
            if foreName:
                authorForeNames.append(foreName)
            authorAffiliations.append(affiliation if affiliation else '¶')
        
        authorForeNameStr = ';'.join(authorForeNames)
        authorAffiliationsStr = '¶'.join(authorAffiliations)
        

        pubType = article.findtext('MedlineCitation/Article/PublicationTypeList/PublicationType')         #Publication Type
        
        
        pubMedRecDate = article.find('PubmedData/History/PubMedPubDate[@PubStatus="received"]')      #PubMedPubDate (received)
        pubMedRec = f"{pubMedRecDate.findtext('Year')}-{pubMedRecDate.findtext('Month')}-{pubMedRecDate.findtext('Day')}" if pubMedRecDate is not None else ''
 
        pubMedAccDate = article.find('PubmedData/History/PubMedPubDate[@PubStatus="accepted"]')      #PubMedPubDate (accepted)
        pubMedAcc = f"{pubMedAccDate.findtext('Year')}-{pubMedAccDate.findtext('Month')}-{pubMedAccDate.findtext('Day')}" if pubMedAccDate is not None else ''


        # Create list for the article data gathered
        articleData = [
            pmid, pubDateYear, journalTitle, journalIso, articleTitle,
            pagination, abstract, authorForeNameStr,
            authorAffiliationsStr, pubType, pubMedRec, pubMedAcc
        ]

        if journalTitle not in journalsData:
            journalsData[journalTitle] = []
        
        journalsData[journalTitle].append(articleData)

    return journalsData


# Function used to create an abbreviation for the output tsv file name
def abbreviateFileName(title):
    words = re.split(r'\W+', title)
    abbreviation = ''.join(word[0].upper() for word in words if word)
    return abbreviation

# Function used to clean a file's name to avoid file name inconsistencies/conflicts
def cleanFileName(name):
    # Replace invalid characters with underscores
    cleanName = re.sub(r'[<>:"/\\|?*]', '_', name)
    cleanName = cleanName.replace(' ', '_')
    # Remove trailing dots or spaces
    cleanName = cleanName.rstrip(". ")
    return cleanName

# Function used to write data out to a .tsv file
def writeToTsv(fileName, data):
    tsvHeader = ['PMID', 'PubDateYear', 'JournalTitle', 'JournalIso',
                  'ArticleTitle', 'Pagination', 'Abstract', 'AuthorForeNames',
                  'AuthorAffiliations', 'PublicationType', 'PubMedPubDate(received)', 'PubMedPubDate(accepted)']
    
    #open tsv file 
    with open(fileName, 'w', newline='', encoding='utf-8') as tsvFile:
        tsvWriter = csv.writer(tsvFile, delimiter='\t')
        tsvWriter.writerow(tsvHeader)                                   # Write header
        tsvWriter.writerows(data)                                       # Write rows

def main():
    gzipFile = 'pubmed24n1219.xml.gz'                                   #Gz file we want to unzip
    xmlFile = 'myfile.xml'                                              #xml file we want to output xml data to 

    extractGzipToXml(gzipFile, xmlFile)                                 #extract and convert to xml
    journalsData = parsePubMedArticles(xmlFile)                         #parse the xml file
    

    #Clean journal/article name and write data to tsv file 
    for journalTitle, articles in journalsData.items():
        abbreviation = abbreviateFileName(journalTitle)
        cleanName = cleanFileName(abbreviation)
        tsvFile= f'{cleanName}.tsv'
        writeToTsv(tsvFile, articles)

if __name__ == "__main__":
    main()
