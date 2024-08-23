import gzip
import shutil
import xml.etree.ElementTree as ET
import csv
import re
from datetime import datetime
from textatistic import Textatistic
import pycountry
import glob
from timeit import default_timer as timer
from datetime import timedelta
from numba import jit
import os
import time
from vars import georgia_municipalities
from vars import institutions
from vars import codes_uppercase

# Function used to excract .gz file and copy over to .xml file to be able to parse data
def extractGzipToXml(gzipFile, xmlFile):
    with gzip.open(gzipFile, 'rb') as fin:
        with open(xmlFile, 'wb') as fout:
            shutil.copyfileobj(fin, fout)


# Load the gender data into dictionaries
def loadGenderData(filePath):
    gender_data = {}
    with open(filePath, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        for row in reader:
            name = row[0].strip().lower()
            gender = row[1].strip().lower()
            prob = float(row[2].strip())
            gender_data[name] = (gender, prob)
    return gender_data

# Load the genderize.io data
gender_data = loadGenderData('output_genderize.csv')

# Function to determine the gender of a name based on the genderize data
def determineGender(name):
    if not name:
        return "-"

    name = re.sub(r'\s.+', '', name)  # Keep only the first word
    name = re.sub(r'[\"\>\`\´]', '', name)  # Remove specific punctuation marks
    name = re.sub(r'^\-', '', name)  # Remove leading hyphens

    # Convert special characters to normal characters
    name = re.sub(r'[áàäâã]', 'a', name)
    name = re.sub(r'[éèëê]', 'e', name)
    name = re.sub(r'[íìïî]', 'i', name)
    name = re.sub(r'[óòöôõø]', 'o', name)
    name = re.sub(r'[úùüû]', 'u', name)
    name = re.sub(r'[ÁÀÄÂÃÅ]', 'A', name)
    name = re.sub(r'[ÉÈËÊ]', 'E', name)
    name = re.sub(r'[ÍÌÏÎ]', 'I', name)
    name = re.sub(r'[ÓÒÖÔÕØ]', 'O', name)
    name = re.sub(r'[ÚÙÜÛ]', 'U', name)
    name = re.sub(r'š', 's', name)
    name = re.sub(r'Š', 'S', name)
    name = re.sub(r'ñ', 'n', name)
    name = re.sub(r'Ñ', 'N', name)
    name = re.sub(r'ç', 'c', name)
    name = re.sub(r'Ç', 'C', name)

    # Default output for various conditions
    out = "?"
    if name == "":
        return "-"
    if re.search(r'\.|^\w$', name) or (not re.search(r'[a-z]', name) and len(name) < 4):
        return "I"

    # Look up gender and probability
    name = name.lower()  # Convert to lowercase
    if name in gender_data:
        gender, prob = gender_data[name]
        if gender == "male" and prob >= 0.9:
            out = "M"
        elif gender == "female" and prob >= 0.9:
            out = "F"
        elif gender in ["male", "female"] and prob < 0.9:
            out = "U"

    return out

# Prepare a list of country names and their common variations using pycountry
def getCountryVariations():
    countryVariations = {}
    for country in pycountry.countries:
        countryVariations[country.name.lower()] = country.name
        if hasattr(country, 'official_name'):
            countryVariations[country.official_name.lower()] = country.name
        for name in getattr(country, 'common_name', []):
            if len(name) > 1:
                countryVariations[name.lower()] = country.name

   # Add common variations and missing country names manually
    additional_countries = {
    'united states': 'United States', 'united states of america': 'United States',
    'uk': 'United Kingdom', 'united kingdom': 'United Kingdom', 'england': 'United Kingdom', 'great britain': 'United Kingdom',
    'south korea': 'South Korea', 'republic of korea': 'South Korea', 'korea': 'South Korea',
    'north korea': 'North Korea', 'democratic people\'s republic of korea': 'North Korea',
    'russia': 'Russia', 'russian federation': 'Russia', 'iran': 'Iran', 'islamic republic of iran': 'Iran',
    'hong kong': 'Hong Kong', 'hong kong sar': 'Hong Kong', 'taiwan': 'Taiwan', 'republic of china': 'Taiwan',
    'czech republic': 'Czechia', 'czechia': 'Czechia', 'slovak republic': 'Slovakia', 'slovakia': 'Slovakia',
    'turkey': 'Turkey', 'vatican city': 'Vatican City', 'holy see': 'Vatican City',
    'macau': 'Macau', 'macao': 'Macau', 'saudi arabia': 'Saudi Arabia', 'alabama': 'United States',
    'alaska': 'United States', 'arizona': 'United States', 'arkansas': 'United States',
    'california': 'United States', 'colorado': 'United States','connecticut': 'United States', 'delaware': 'United States', 
    'florida': 'United States', 'hawaii': 'United States', 'idaho': 'United States', 
    'illinois': 'United States', 'indiana': 'United States', 'iowa': 'United States', 'kansas': 'United States',
    'kentucky': 'United States', 'louisiana': 'United States', 'maine': 'United States', 'maryland': 'United States',
    'massachusetts': 'United States', 'michigan': 'United States', 'minnesota': 'United States', 'mississippi': 'United States',
    'missouri': 'United States', 'montana': 'United States', 'nebraska': 'United States', 'nevada': 'United States',
    'new hampshire': 'United States', 'new jersey': 'United States', 'new mexico': 'United States', 'new york': 'United States',
    'north carolina': 'United States', 'north dakota': 'United States', 'ohio': 'United States', 'oklahoma': 'United States',
    'oregon': 'United States', 'pennsylvania': 'United States', 'rhode island': 'United States', 'south carolina': 'United States',
    'south dakota': 'United States', 'tennessee': 'United States', 'texas': 'United States', 'utah': 'United States',
    'vermont': 'United States', 'virginia': 'United States', 'washington': 'United States', 'west virginia': 'United States',
    'wisconsin': 'United States', 'wyoming': 'United States', 'españa': 'Spain', 'australian': 'Australia', 'chinese': 'China','beijing': 'China',
    'boston': 'United States', 'london': 'United Kingdom', 'barcelona': 'Spain', 'maroc': 'Morocco', 'méxico': 'Mexico', 'palestine': 'Palestine',
    'schweiz': 'Switzerland', 'shanghai': 'China', 'tanzania': 'Tanzania', 'syria': 'Syria', 'tunisie': 'Tunisia', 'turkiye': 'Turkey',
    'u k': 'United Kingdom', 'u s a': 'United States', 'vietnam': 'Viet Nam', "österreich": "Austria", "osterreich": "Austria", "belgië": "Belgium",
    "belgique": "Belgium", "brasil": "Brazil", "deutschland": "Germany", "italia": "Italy", "nederland": "Netherlands", "panamá": "Panama", "perú": "Peru",
    "polska": "Poland", "suisse": "Switzerland", "chine": "China"
    }

    countryVariations.update(additional_countries)

    return countryVariations

country_variations = getCountryVariations()


# Function to clean the affiliation string by removing punctuation marks
def cleanAffiliation(affiliation):
    return re.sub(r'[^\w\s]', '', affiliation)


# Function to find the country in an affiliation string
def findCountry(affiliation):
    if not affiliation:
        return "NA"

    # Clean the affiliation
    words = affiliation.split()
    words = [word for word in words if "@" not in word]
    affiliation = ' '.join(words)

    for i in range (10):
        affiliation = affiliation.replace(str(i), " ")

    affiliation = affiliation.replace("(", " ")
    affiliation = affiliation.replace(")", " ")
    affiliation = affiliation.replace("-", " ")
    affiliation = affiliation.replace(".", " ")
    affiliation = affiliation.replace(",", " ")
    affiliation = affiliation.replace(";", " ")

    affiliation = " " + affiliation + " "
    affiliation_upper = affiliation
    affiliation = affiliation.lower()

    # Check if 'Georgia' is the country and if it's ambiguous
    if " georgia " in affiliation:  
        for city in georgia_municipalities:
            if " " + city.lower() + " " in affiliation:
                affiliation += " usa "
                affiliation_upper += " USA "
                break
        if " usa " not in affiliation:
            for institution in institutions:
                if " " + institution.lower() + " " in affiliation:
                    affiliation += " usa "
                    affiliation_upper += " USA "
                    break
        if " agmashenebeli " in affiliation or " kutaisi " in affiliation or " tbilisi " in affiliation or " batumi " in affiliation or " gori " in affiliation or " elavi " in affiliation or " poti " in affiliation or " zugdidi " in affiliation or " rustavi " in affiliation:
            affiliation += " georgia "
            affiliation_upper += " georgia "

    # Check if it's in the state of New Mexico or New Jersey
    if " new mexico " in affiliation or " new jersey " in affiliation:
        affiliation += " usa "
        affiliation_upper += " USA "

    # Use find() method to determine the position of the country names
    country = ""
    pos = -1  # Use -1 to indicate no match found
   
    for key in country_variations.keys():
        pos2 = affiliation.rfind(" "+key+" ")
        if pos2 > pos:
            pos = pos2
            country = country_variations[key]

    for key in codes_uppercase.keys():
        pos2 = affiliation_upper.rfind(" "+key+" ")
        if pos2 > pos:
            pos = pos2
            country = codes_uppercase[key]

    if country == "":
        return "NA"
    else:
        return country 

# Function to calculate the number of pages based on pagination
def calculatePages(pagination):
    if not pagination or '-' not in pagination:
        return "NA"
    
    # Check for multiple ranges/values and discard if present
    if ',' in pagination or ';' in pagination or ' ' in pagination:
        return "NA"
    
    # Remove everything after '.' if it exists
    pagination = pagination.split('.')[0]

    # Remove letters and special characters
    pagination = re.sub(r'[^\d\-]', '', pagination)
    if pagination == "-":
        return "NA"

    # Split the pagination by '-' and ensure there are exactly two values
    parts = pagination.split('-')
    if len(parts) != 2:
        return "NA"

    start_page, end_page = parts
    try:
        # Handle cases like 1378-88
        if len(start_page) > len(end_page):
            end_page = start_page[:len(start_page)-len(end_page)] + end_page

        start_page = int(start_page)
        end_page = int(end_page)

        return end_page - start_page + 1
    except ValueError:
        return "NA"

# Ensure the abstract ends with proper punctuation
def ensureProperPunctuation(abstract):
    # Check for common abbreviations that might cause issues
    if re.search(r'\b(?:etc|i\.e|e\.g)\.$', abstract.strip()):
        abstract += '.'
    elif abstract and not re.match(r'.*[\.\!\?\"\'”’]$', abstract.strip()):
        abstract += '.'
    return abstract

#@jit(nopython = True)
#def getTextTest(abstract):
#    return Textatistic(abstract)

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
        numPages = calculatePages(pagination)

        # Concatenate all abstract sections using itertext()
        abstract_sections = article.findall('MedlineCitation/Article/Abstract/AbstractText')
        abstract = ' '.join(ET.tostring(section, encoding='unicode', method='text').strip() for section in abstract_sections)

        if not abstract:
            abstract = "NA"

        if abstract == "NA":
            daleChallScore = fleschScore = fleschKinCaidScore = gunningFogScore = smogScore = "NA"
        else:
            try:    
                abstract = ensureProperPunctuation(abstract) 
                scores = Textatistic(abstract)
                daleChallScore = scores.dalechall_score
                fleschScore = scores.flesch_score
                fleschKinCaidScore = scores.fleschkincaid_score
                gunningFogScore = scores.gunningfog_score
                smogScore = scores.smog_score
            except Exception as e:
                daleChallScore = fleschScore = fleschKinCaidScore = gunningFogScore = smogScore = "NA"
                
                

            



        #Create list for author forenames, affiliations and gender
        authorForeNames = []
        authorAffiliations = []
        authorGenders = []

        # Initialize author gender counters
        numberFemaleAuthors = 0
        numberMaleAuthors = 0
        numberUnisexAuthors = 0
        numberUnknownAuthors = 0  
        fractionFemaleAuthors = "NA"
        genderFirstAuthor = "NA"
        genderLastAuthor = "NA"
        genderLastCorrespondingAuthor = "NA"
        countryFirstAuthor = "NA"
        countryLastAuthor = "NA"
        countryLastCorrespondingAuthor = "NA"
        
         # For every author found in the articles, collect forenames and affiliations
        for idx, author in enumerate(article.findall('MedlineCitation/Article/AuthorList/Author')):
            foreName = author.findtext('ForeName')
            affiliation = author.findtext('AffiliationInfo/Affiliation')
            if foreName:
                authorForeNames.append(foreName)
                gender = determineGender(foreName)
                authorGenders.append(gender)
                country = findCountry(affiliation)
                if idx == 0:
                    genderFirstAuthor = gender
                    countryFirstAuthor = country
                if idx == len(article.findall('MedlineCitation/Article/AuthorList/Author')) - 1:
                    genderLastAuthor = gender
                    countryLastAuthor = country
                if "@" in (affiliation or ""):
                    genderLastCorrespondingAuthor = gender
                    countryLastCorrespondingAuthor = country

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
        
        if numberFemaleAuthors + numberMaleAuthors > 0:
            fractionFemaleAuthors = numberFemaleAuthors / (numberFemaleAuthors + numberMaleAuthors)
        else:
            fractionFemaleAuthors = "NA"
        
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
            try:
                recDate = datetime.strptime(pubMedRec, '%Y-%m-%d')
                accDate = datetime.strptime(pubMedAcc, '%Y-%m-%d')
                timeUnderReview = (accDate - recDate).days
            except ValueError as e:
                timeUnderReview = "NA"


        # Create list for the article data gathered
        articleData = [
            pmid, pubDateYear, journalTitle, journalIso, articleTitle,
            pagination, numPages, abstract, authorForeNameStr,
            authorAffiliationsStr, genderFirstAuthor, genderLastAuthor, genderLastCorrespondingAuthor,
            countryFirstAuthor, countryLastAuthor, countryLastCorrespondingAuthor,
            numberFemaleAuthors, numberMaleAuthors, numberUnisexAuthors, 
            numberUnknownAuthors, fractionFemaleAuthors, pubType, pubMedRec, pubMedAcc, timeUnderReview,
            daleChallScore, fleschScore, fleschKinCaidScore, gunningFogScore, smogScore,
        ]

        if journalIso not in journalsData:
            journalsData[journalIso] = []
        
        journalsData[journalIso].append(articleData)

    return journalsData



# Function used to clean a file's name to avoid file name inconsistencies/conflicts
def cleanFileName(name):
    # Ensure the input is a string
    name = str(name)
    # Replace invalid characters with underscores
    cleanName = re.sub(r'[<>:"/\\|?*]', '_', name)
    cleanName = cleanName.replace(' ', '_')
    # Remove trailing dots or spaces
    cleanName = cleanName.rstrip(". ")
    return cleanName

# Function used to write data out to a .tsv file
def writeToTsv(fileName, data):
    tsvHeader = ['PMID', 'PubDateYear', 'JournalTitle', 'JournalIso', 
                  'ArticleTitle', 'Pagination', 'NumPages', 'Abstract', 'AuthorForeNames', 
                  'AuthorAffiliations', 'GenderFirstAuthor', 'GenderLastAuthor', 'GenderLastCorrespondingAuthor', 
                  'CountryFirstAuthor', 'CountryLastAuthor', 'CountryLastCorrespondingAuthor', 
                  'NumberFemaleAuthors', 'NumberMaleAuthors', 'NumberUnisexAuthor', 
                  'NumberUnknownAuthors', 'FractionFemaleAuthors', 'PublicationType', 
                  'PubMedPubDate(received)', 'PubMedPubDate(accepted)', 'TimeUnderReview(days)', 
                  'DaleChallScore', 'FleschScore', 'FleschKinCaidScore', 'GunningFogScore', 'SmogScore']
    
    file_exists = os.path.isfile(fileName)

    # Open tsv file in append mode if it exists, otherwise write mode
    with open(fileName, 'a' if file_exists else 'w', newline='', encoding='utf-8') as tsvFile:
        tsvWriter = csv.writer(tsvFile, delimiter='\t')
        if not file_exists:
            tsvWriter.writerow(tsvHeader)  # Write header if file does not exist
        tsvWriter.writerows(data)  # Write rows


# Function to write problematic abstracts to a TSV file
def writeProblematicAbstracts(fileName, data):
    tsvHeader = ['PMID', 'Abstract', 'JournalISO']
    # Open tsv file 
    with open(fileName, 'w', newline='', encoding='utf-8') as tsvFile:
        tsvWriter = csv.writer(tsvFile, delimiter='\t')
        tsvWriter.writerow(tsvHeader)  # Write header
        tsvWriter.writerows(data)  # Write rows

def main():

    
    start = timer()

    for gzipFile in glob.glob('./xmlFiles/pubmed24n*.xml.gz'):
        xmlFile = gzipFile.replace('.xml.gz', '.xml')

        extractGzipToXml(gzipFile, xmlFile)                                 # Extract and convert to xml
        
        t1 = time.time()

        journalsData = parsePubMedArticles(xmlFile)                         # Parse the xml file

        t2 = time.time()
        print("Total time to parse " + xmlFile + ": " + str(t2-t1))

        t3 = time.time()
        # Clean journal/article name and write data to tsv file 
        for journalIso, articles in journalsData.items():
            cleanName = cleanFileName(journalIso)
            tsvFile= f'./tsvFiles/{cleanName}.tsv'
            writeToTsv(tsvFile, articles)

        t4 = time.time()
        print("Total time to write to .tsv files: " + str(t4-t3))
        os.remove(xmlFile)

    end = timer()
    print("Total time for script to run: " + str(timedelta(seconds=end-start)))

if __name__ == "__main__":
    main()
