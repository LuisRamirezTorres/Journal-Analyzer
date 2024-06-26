import gzip
import shutil
import xml.etree.ElementTree as ET
import csv
import re
from datetime import datetime

# Function used to excract .gz file and copy over to .xml file to be able to parse data
def extractGzipToXml(gzipFile, xmlFile):
    with gzip.open(gzipFile, 'rb') as fin:
        with open(xmlFile, 'wb') as fout:
            shutil.copyfileobj(fin, fout)


# Load the name-gender dataset into a dictionary
def loadGenderData(filePath):
    genderCount = {}
    with open(filePath, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        for row in reader:
            name = row[0].strip().lower()
            gender = row[1].strip()
            count = int(row[2].strip())
            genderCount[(name, gender)] = count
    return genderCount

gender_count = loadGenderData('name_gender_dataset.csv')

# Function to clean the name similar to the Perl script created by Dr. David Alvarez-Ponce
def cleanName(name):
    name = re.sub(r'[\"áàäâã]', 'a', name)
    name = re.sub(r'[éèëê]', 'e', name)
    name = re.sub(r'[íìïî]', 'i', name)
    name = re.sub(r'[óòöôø]', 'o', name)
    name = re.sub(r'[úùüû]', 'u', name)
    name = re.sub(r'[ÁÀÄÂÅ]', 'A', name)
    name = re.sub(r'[ÉÈËÊ]', 'E', name)
    name = re.sub(r'[ÍÌÏÎ]', 'I', name)
    name = re.sub(r'[ÓÒÖÔØ]', 'O', name)
    name = re.sub(r'[ÚÙÜÛ]', 'U', name)
    name = re.sub(r'š', 's', name)
    name = re.sub(r'ñ', 'n', name)
    name = re.sub(r'ç', 'c', name)
    name = name.lower()
    
    nameParts = name.split()
    for part in nameParts:
        if '.' not in part and len(part) != 1:
            return part
    return name



# Function to determine the gender of a name
def determineGender(name):
    name = cleanName(name)
    
    out = "?"
    male_count = gender_count.get((name, "M"), 0)
    female_count = gender_count.get((name, "F"), 0)
    
    if male_count > 0 and female_count == 0:
        out = "M"
    elif female_count > 0 and male_count == 0:
        out = "F"
    elif male_count > 0 and female_count > 0:
        out = "U"
        if male_count / (male_count + female_count) > 2 / 3:
            out = "M"
        elif female_count / (male_count + female_count) > 2 / 3:
            out = "F"
    
    return out

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



        #Create list for author forenames, affiliations and gender
        authorForeNames = []
        authorAffiliations = []
        authorGenders = []

        # Initialize author gender counters
        numberFemaleAuthors = 0
        numberMaleAuthors = 0
        numberUnisexAuthors = 0
        numberUnknownAuthors = 0
        genderFirstAuthor = None
        genderLastCorrespondingAuthor = None
        
         # For every author found in the articles, collect forenames and affiliations
        for idx, author in enumerate(article.findall('MedlineCitation/Article/AuthorList/Author')):
            foreName = author.findtext('ForeName')
            affiliation = author.findtext('AffiliationInfo/Affiliation')
            if foreName:
                authorForeNames.append(foreName)
                gender = determineGender(foreName)
                authorGenders.append(gender)
                if idx == 0:
                    genderFirstAuthor = gender
                if "@" in (affiliation or ""):
                    genderLastCorrespondingAuthor = gender

                if gender == "F":
                    numberFemaleAuthors += 1
                elif gender == "M":
                    numberMaleAuthors += 1
                elif gender == "U":
                    numberUnisexAuthors += 1
                else:
                    numberUnknownAuthors += 1
            else:
                numberUnknownAuthors += 1

            authorAffiliations.append(affiliation if affiliation else '0')
        
        if genderLastCorrespondingAuthor is None and authorGenders:
            genderLastCorrespondingAuthor = authorGenders[-1]
        
        authorForeNameStr = ';'.join(authorForeNames)
        authorAffiliationsStr = '¶'.join(authorAffiliations)
        

        pubType = article.findtext('MedlineCitation/Article/PublicationTypeList/PublicationType')           #Publication Type

                                                                                                            #PubMed received and accepted dates
        pubMedRecDate = article.find('PubmedData/History/PubMedPubDate[@PubStatus="received"]')
        pubMedRec = None
        if pubMedRecDate is not None:
            pubMedRec = f"{pubMedRecDate.findtext('Year')}-{pubMedRecDate.findtext('Month')}-{pubMedRecDate.findtext('Day')}"
        
        pubMedAccDate = article.find('PubmedData/History/PubMedPubDate[@PubStatus="accepted"]')
        pubMedAcc = None
        if pubMedAccDate is not None:
            pubMedAcc = f"{pubMedAccDate.findtext('Year')}-{pubMedAccDate.findtext('Month')}-{pubMedAccDate.findtext('Day')}"
        
        timeUnderReview = None
        if pubMedRec and pubMedAcc:
            recDate = datetime.strptime(pubMedRec, '%Y-%m-%d')
            accDate = datetime.strptime(pubMedAcc, '%Y-%m-%d')
            timeUnderReview = (accDate - recDate).days


        # Create list for the article data gathered
        articleData = [
            pmid, pubDateYear, journalTitle, journalIso, articleTitle,
            pagination, abstract, authorForeNameStr,
            authorAffiliationsStr, genderFirstAuthor, genderLastCorrespondingAuthor,
            numberFemaleAuthors, numberMaleAuthors, numberUnisexAuthors, 
            numberUnknownAuthors, pubType, pubMedRec, pubMedAcc, timeUnderReview
        ]

        if journalIso not in journalsData:
            journalsData[journalIso] = []
        
        journalsData[journalIso].append(articleData)

    return journalsData



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
                  'AuthorAffiliations', 'GenderFirstAuthor', 'GenderLastCorrespondingAuthor',
                  'NumberFemalAuthors', 'NumberMaleAuthors', 'NumberUnisexAuthor', 
                  'NumberUnknownAuthors', 'PublicationType', 'PubMedPubDate(received)', 'PubMedPubDate(accepted)', 'TimeUnderReview (days)']
    
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
    for journalIso, articles in journalsData.items():
        cleanName = cleanFileName(journalIso)
        tsvFile= f'{cleanName}.tsv'
        writeToTsv(tsvFile, articles)

if __name__ == "__main__":
    main()
