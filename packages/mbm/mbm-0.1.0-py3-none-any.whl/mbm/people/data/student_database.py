"""
Student Data - Organized by Branch

Complete student database for MBM University.
Each student has unique identifier for CLI commands.

Generated from official student records.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class Branch(Enum):
    """Engineering branches at MBM University."""
    AI_DS = "Artificial Intelligence and Data Science"
    CHEMICAL = "Chemical Engineering"
    CIVIL = "Civil Engineering"
    CSE = "Computer Science & Engineering"
    EE = "Electrical Engineering"
    ECE = "Electronics & Communication Engineering"
    ECC = "Electronics & Computer Engineering"
    EEE = "Electronics & Electrical Engineering"
    IT = "Information Technology"
    ME = "Mechanical Engineering"
    MINING = "Mining Engineering"
    PETROLEUM = "Petroleum Engineering"
    PIE = "Production & Industrial Engineering"


@dataclass
class Student:
    """Student record with all details."""
    name: str
    dob: str  # Format: DD/MM/YYYY
    registration_no: str
    enrollment_no: str
    branch: Branch
    identifier: str = field(default="")  # CLI command identifier
    
    def __post_init__(self):
        """Generate identifier from name if not provided."""
        if not self.identifier:
            # Create unique identifier from name
            # Handle duplicate names by appending registration suffix
            self.identifier = self._generate_identifier()
    
    def _generate_identifier(self) -> str:
        """Generate URL-safe identifier from name."""
        # Remove special characters, convert to lowercase
        name = self.name.lower().strip()
        # Replace spaces with underscores for multi-word names
        name = name.replace(" ", "_").replace(".", "").replace("'", "")
        # Remove any non-alphanumeric except underscore
        identifier = "".join(c for c in name if c.isalnum() or c == "_")
        return identifier


# =============================================================================
# STUDENT DATA BY BRANCH
# =============================================================================

# -----------------------------------------------------------------------------
# 1. ARTIFICIAL INTELLIGENCE AND DATA SCIENCE (AI & DS) - 27 Students
# -----------------------------------------------------------------------------
AI_DS_STUDENTS: List[Student] = [
    Student("AADITYA MEHTA", "1/10/2003", "23UFIA1001", "MBMU22/0303", Branch.AI_DS),
    Student("ANKIT KUMAR", "18/12/2003", "23UFIA1060", "MBMU22/0305", Branch.AI_DS),
    Student("ANUJ AGRAWAL", "6/7/2004", "23UFIA1075", "MBMU22/0306", Branch.AI_DS),
    Student("ARYAN GURJAR", "17/12/2004", "23UFIA1090", "MBMU22/0307", Branch.AI_DS),
    Student("DARSHIL PUNGALIA", "12/2/2005", "23UFIA1139", "MBMU22/0308", Branch.AI_DS),
    Student("DEEPAK", "3/5/2004", "23UFIA1145", "MBMU22/0309", Branch.AI_DS, "deepak_aids"),
    Student("DIVYANSHU KAROLIWAL", "5/11/2003", "23UFIA1176", "MBMU22/0310", Branch.AI_DS),
    Student("DIYA GAUR", "10/6/2004", "23UFIA1177", "MBMU22/0518", Branch.AI_DS),
    Student("GARVIT JAIN", "2/3/2003", "23UFIA1184", "MBMU22/0519", Branch.AI_DS),
    Student("HARDIKA MAKWANA", "13/12/2003", "23UFIA1200", "MBMU22/0529", Branch.AI_DS),
    Student("HIMANSHU DHAKER", "25/11/2003", "23UFIA1225", "MBMU22/0311", Branch.AI_DS),
    Student("ISHITA DHARIWAL", "30/08/2002", "23UFIA1238", "MBMU22/0312", Branch.AI_DS),
    Student("JASRAJ CHOUHAN", "8/5/2002", "23UFIA1244", "MBMU22/0313", Branch.AI_DS),
    Student("KOMAL PURBIA", "3/9/2002", "23UFIA1288", "MBMU22/0314", Branch.AI_DS),
    Student("KRISH MEHTA", "16/02/2004", "23UFIA1291", "MBMU22/0315", Branch.AI_DS),
    Student("MANISH KUMAR", "11/5/2005", "23UFIE2031", "MBMU22/0316", Branch.AI_DS),
    Student("MUKAND JIRAWLA", "27/01/2005", "23UFIE2031", "MBMU22/0317", Branch.AI_DS),
    Student("NARENDRA GURJAR", "9/11/2002", "23UFIE2042", "MBMU22/0318", Branch.AI_DS),
    Student("NEHA SHARMA", "6/8/2003", "23UFIE2049", "MBMU22/0492", Branch.AI_DS),
    Student("NILESH ANJANA", "12/10/2002", "23UFIE2059", "MBMU22/0319", Branch.AI_DS),
    Student("RAMSWAROOP MEENA", "27/08/2004", "23UFIE2142", "MBMU22/0320", Branch.AI_DS),
    Student("RIPUDAMAN SINGH PALAWAT", "6/11/2003", "23UFIE2153", "MBMU22/0321", Branch.AI_DS),
    Student("SIDDHESH KUMAR", "4/11/2003", "23UFIE2225", "MBMU22/0322", Branch.AI_DS),
    Student("SIDHARTH JOSHI", "31/03/2003", "23UFIE2226", "MBMU22/0493", Branch.AI_DS),
    Student("SONIYA KUMARI SAINI", "29/04/2004", "23UFIE2234", "MBMU22/0323", Branch.AI_DS),
    Student("VEDIKA SHARMA", "28/01/2004", "23UFIE2296", "MBMU22/0324", Branch.AI_DS),
    Student("YUVRAJ SINGH", "6/9/2004", "23UFIE2338", "MBMU22/0325", Branch.AI_DS, "yuvraj_singh_aids"),
]

# -----------------------------------------------------------------------------
# 2. CHEMICAL ENGINEERING - 17 Students
# -----------------------------------------------------------------------------
CHEMICAL_STUDENTS: List[Student] = [
    Student("ANKIT SHARMA", "7/9/2003", "23UFIA1063", "MBMU22/0166", Branch.CHEMICAL, "ankit_sharma_chem"),
    Student("ANSHUMAN TAPARIA", "14/12/2003", "23UFIA1074", "MBMU22/0167", Branch.CHEMICAL),
    Student("CHANCHAL KANWAR", "25/02/2004", "23UFIA1127", "MBMU22/0168", Branch.CHEMICAL),
    Student("CHITRAKSHI BISHNOI", "1/9/2004", "23UFIA1135", "MBMU22/0169", Branch.CHEMICAL),
    Student("GARVIT BHATI", "19/03/2004", "23UFIA1183", "MBMU22/0170", Branch.CHEMICAL),
    Student("JAIVARDHAN SINGH BALOT", "30/04/2005", "23UFIA1241", "MBMU22/0171", Branch.CHEMICAL),
    Student("KHUSHI KANWAR", "27/06/2003", "23UFIA1279", "MBMU22/0172", Branch.CHEMICAL),
    Student("KUNDAN BOHRA", "13/11/2003", "23UFIA1304", "MBMU22/0173", Branch.CHEMICAL),
    Student("MANYA SINGHVI", "17/09/2003", "23UFIE2004", "MBMU22/0174", Branch.CHEMICAL),
    Student("PIYUSH PARIHAR", "8/12/2004", "23UFIE2080", "MBMU22/0175", Branch.CHEMICAL),
    Student("RAHUL MAKWANA", "31/08/2003", "23UFIE2125", "MBMU22/0176", Branch.CHEMICAL),
    Student("RAMNIWAS VISHNOI", "5/3/2003", "23UFIE2141", "MBMU22/0177", Branch.CHEMICAL),
    Student("RANU SHARMA", "5/1/2005", "23UFIE2143", "MBMU22/0178", Branch.CHEMICAL),
    Student("RISHI ARORA", "21/10/2003", "23UFIE2157", "MBMU22/0179", Branch.CHEMICAL),
    Student("SAGAR ATAL", "16/04/2005", "23UFIE2184", "MBMU22/0180", Branch.CHEMICAL),
    Student("SAPNA POHWANI", "7/10/2002", "23UFIE2199", "MBMU22/0181", Branch.CHEMICAL),
    Student("SONIYA MAKWANA", "7/6/2002", "23UFIE2235", "MBMU22/0182", Branch.CHEMICAL),
]

# -----------------------------------------------------------------------------
# 3. CIVIL ENGINEERING - 41 Students
# -----------------------------------------------------------------------------
CIVIL_STUDENTS: List[Student] = [
    Student("AAKASH", "14/06/2003", "23UFIA1003", "MBMU22/0001", Branch.CIVIL),
    Student("ABHIJEET SINGH", "15/05/2005", "23UFIA1014", "MBMU22/0383", Branch.CIVIL),
    Student("ABHISHEK SINGH RAJPUROHIT", "2/1/2004", "23UFIA1022", "MBMU22/0537", Branch.CIVIL),
    Student("ADITYA SINGH CHOUHAN", "9/2/2005", "23UFIA1025", "MBMU22/0384", Branch.CIVIL),
    Student("AKANKSHA", "2/11/2005", "23UFIA1030", "MBMU22/0502", Branch.CIVIL),
    Student("ANISH BORAKH", "1/1/2005", "23UFIA1050", "MBMU22/0385", Branch.CIVIL),
    Student("ANJALI SHRIMALI", "26/11/2002", "23UFIA1054", "MBMU22/0386", Branch.CIVIL),
    Student("ANJU", "15/11/2005", "23UFIA1055", "MBMU22/0387", Branch.CIVIL),
    Student("ANKIT GURJAR", "25/06/2005", "23UFIA1057", "MBMU22/0388", Branch.CIVIL),
    Student("ANKIT SHARMA", "20/03/2005", "23UFIA1062", "MBMU22/0389", Branch.CIVIL, "ankit_sharma_civil"),
    Student("ANSHU BHAMBHU", "17/09/2004", "23UFIA1069", "MBMU22/0390", Branch.CIVIL),
    Student("ANURAG MEENA", "10/8/2004", "23UFIA1080", "MBMU22/0391", Branch.CIVIL),
    Student("AYAN KHAN", "10/8/2006", "23UFIA1104", "MBMU22/0392", Branch.CIVIL),
    Student("BALWINDER SINGH", "4/6/2005", "23UFIA1109", "MBMU22/0393", Branch.CIVIL),
    Student("BHARTI MEENA", "24/06/2004", "23UFIA1114", "MBMU22/0394", Branch.CIVIL),
    Student("BHOOMIKA SINGH", "25/12/2003", "23UFIA1124", "MBMU22/0523", Branch.CIVIL),
    Student("CHARVI KHICHI", "6/8/2004", "23UFIA1131", "MBMU22/0524", Branch.CIVIL),
    Student("CHETANYA SINGH HADA", "23/11/2004", "23UFIA1133", "MBMU22/0395", Branch.CIVIL),
    Student("CHITRALEKHA DAMOR", "13/11/2005", "23UFIA1136", "MBMU22/0396", Branch.CIVIL),
    Student("DARSHITA GOYAL", "9/7/2004", "23UFIA1140", "MBMU22/0397", Branch.CIVIL),
    Student("DEEPAK MEENA", "15/04/2005", "23UFIA1146", "MBMU22/0525", Branch.CIVIL),
    Student("DEV KUMAR MARU", "19/07/2003", "23UFIA1149", "MBMU22/0526", Branch.CIVIL),
    Student("DHARMESH KUMAR VERMA", "13/12/2004", "23UFIA1154", "MBMU22/0398", Branch.CIVIL),
    Student("DIKSHA PANWAR", "16/08/2003", "23UFIA1163", "MBMU22/0399", Branch.CIVIL),
    Student("GAURAV CHOUDHARY", "21/05/2002", "23UFIA1186", "MBMU22/0400", Branch.CIVIL),
    Student("GAURAV KUMAR MEENA", "13/10/2003", "23UFIA1188", "MBMU22/0401", Branch.CIVIL),
    Student("HARSHIT SHARMA", "27/05/2003", "23UFIA1214", "MBMU22/0402", Branch.CIVIL),
    Student("HIMANSHI JARWAL", "1/9/2004", "23UFIA1222", "MBMU22/0403", Branch.CIVIL),
    Student("KIRTI RANI", "26/10/2004", "23UFIA1282", "MBMU22/0404", Branch.CIVIL),
    Student("KISHORE CHOUDHARY", "15/12/2001", "23UFIA1285", "MBMU22/0545", Branch.CIVIL),
    Student("KOMAL CHOUDHARY", "30/11/2004", "23UFIA1286", "MBMU22/0494", Branch.CIVIL),
    Student("KRISHNA VYAS", "17/12/2003", "23UFIA1293", "MBMU22/0405", Branch.CIVIL),
    Student("LUCKY YADAV", "10/4/2006", "23UFIA1318", "MBMU22/0406", Branch.CIVIL),
    Student("MANASVI CHOUDHARY", "27/05/2004", "23UFIA1330", "MBMU22/0407", Branch.CIVIL),
    Student("MANISHA JAKHAR", "12/5/2003", "23UFIA1340", "MBMU22/0408", Branch.CIVIL),
    Student("MANISHA VERMA", "3/7/2005", "23UFIA1341", "MBMU22/0409", Branch.CIVIL),
    Student("MONIKA MEENA", "22/09/2005", "23UFIE2024", "MBMU22/0491", Branch.CIVIL, "monika_meena_civil"),
    Student("PRINCE MEENA", "6/1/2005", "23UFIE2099", "MBMU22/0495", Branch.CIVIL),
    Student("SIMRAN KAUR", "12/8/2004", "23UFIE2227", "MBMU22/0564", Branch.CIVIL),
    Student("SNEHA PUROHIT", "13/08/2004", "23UFIE2231", "MBMU22/0503", Branch.CIVIL),
    Student("TAMANNA CHOUDHARY", "28/09/2004", "23UFIE2260", "MBMU22/0515", Branch.CIVIL),
]

# -----------------------------------------------------------------------------
# 4. COMPUTER SCIENCE & ENGINEERING (CSE) - 48 Students
# -----------------------------------------------------------------------------
CSE_STUDENTS: List[Student] = [
    Student("AASHITA BHANDARI", "21/05/2004", "23UFIA1005", "MBMU22/0536", Branch.CSE),
    Student("ADITYA VYAS", "25/09/2004", "23UFIA1026", "MBMU22/0240", Branch.CSE),
    Student("AJEET JAIN", "29/03/2004", "23UFIA1029", "MBMU22/0540", Branch.CSE),
    Student("AKASH PARMAR", "24/08/2003", "23UFIA1031", "MBMU22/0541", Branch.CSE),
    Student("ARYAN SWARNKAR", "27/10/2003", "23UFIA1094", "MBMU22/0543", Branch.CSE),
    Student("ASAN ALI", "20/03/2003", "23UFIA1095", "MBMU22/0241", Branch.CSE),
    Student("AYUSH CHOUHAN", "4/8/2004", "23UFIA1106", "MBMU22/0544", Branch.CSE),
    Student("BHARAT SINGH RAJPUT", "16/03/2004", "23UFIA1112", "MBMU22/0213", Branch.CSE),
    Student("DAKSHAY SINGH BHATI", "27/11/2002", "23UFIA1137", "MBMU22/0214", Branch.CSE),
    Student("GARIMA CHOUDHARY", "2/11/2003", "23UFIA1182", "MBMU22/0546", Branch.CSE),
    Student("GUNGUN GURJAR", "19/11/2007", "23UFIA1195", "MBMU22/0215", Branch.CSE),
    Student("HARSH RAJANI", "11/5/2003", "23UFIA1202", "MBMU22/0559", Branch.CSE),
    Student("HARSHITA ATAL", "12/10/2004", "23UFIA1216", "MBMU22/0547", Branch.CSE),
    Student("HEM SINGH", "5/3/2004", "23UFIA1219", "MBMU22/0216", Branch.CSE),
    Student("HIMESH PARASHAR", "9/1/2004", "23UFIA1228", "MBMU22/0217", Branch.CSE),
    Student("ISHA MEENA", "24/11/2004", "23UFIA1233", "MBMU22/0218", Branch.CSE),
    Student("ISHA PANDEY", "13/10/2003", "23UFIA1234", "MBMU22/0504", Branch.CSE),
    Student("KALLU KUMARI", "7/4/2004", "23UFIA1258", "MBMU22/0219", Branch.CSE),
    Student("KANISHKA SINGHAL", "20/01/2005", "23UFIA1261", "MBMU22/0220", Branch.CSE),
    Student("KAVITA JAKHAR", "7/4/2005", "23UFIA1270", "MBMU22/0221", Branch.CSE),
    Student("KULDEEP KANWAR", "4/4/2002", "23UFIA1297", "MBMU22/0548", Branch.CSE),
    Student("KUSHAL DODIYAR", "5/4/2005", "23UFIA1306", "MBMU22/0242", Branch.CSE),
    Student("LAXITA DETWAL", "24/03/2004", "23UFIA1314", "MBMU22/0222", Branch.CSE),
    Student("MAHENDRA GURJAR", "3/7/2003", "23UFIA1323", "MBMU22/0223", Branch.CSE),
    Student("MAHESH KUMAR", "16/05/2002", "23UFIA1327", "MBMU22/0224", Branch.CSE),
    Student("MANAV JHA", "22/10/2003", "23UFIA1331", "MBMU22/0225", Branch.CSE),
    Student("MANISH RAHI", "7/2/2004", "23UFIA1336", "MBMU22/0226", Branch.CSE),
    Student("NEERAJ GUPTA", "3/12/2002", "23UFIE2044", "MBMU22/0549", Branch.CSE),
    Student("NIKHIL SWAMI", "24/02/2003", "23UFIE2055", "MBMU22/0227", Branch.CSE),
    Student("PINKI", "17/08/2004", "23UFIE2075", "MBMU22/0228", Branch.CSE),
    Student("PRABHBIR SINGH JUNEJA", "13/10/2003", "23UFIE2086", "MBMU22/0229", Branch.CSE),
    Student("PREETI YADAV", "14/12/2003", "23UFIE2095", "MBMU22/0230", Branch.CSE),
    Student("PRINCE DAYMA", "23/07/2004", "23UFIE2098", "MBMU22/0231", Branch.CSE),
    Student("PRIYANSHU KALAL", "18/03/2002", "23UFIE2106", "MBMU22/0496", Branch.CSE),
    Student("PUSHKAR SINGH", "24/01/2003", "23UFIE2110", "MBMU22/0232", Branch.CSE),
    Student("RAJAT GAUR", "27/10/2001", "23UFIE2129", "MBMU22/0550", Branch.CSE),
    Student("RAKSHIT PANDYA", "25/10/2003", "23UFIE2136", "MBMU22/0233", Branch.CSE),
    Student("RISHABH JAJU", "11/11/2004", "23UFIE2155", "MBMU22/0234", Branch.CSE),
    Student("ROHIT PANWAR", "27/06/2004", "23UFIE2174", "MBMU22/0235", Branch.CSE),
    Student("SAKSHI SINGHAL", "12/9/2004", "23UFIE2187", "MBMU22/0551", Branch.CSE),
    Student("SHASHANK RAJPUROHIT", "13/08/2003", "23UFIE2211", "MBMU22/0552", Branch.CSE),
    Student("SUMAN RAJBOHRA", "20/06/2004", "23UFIE2245", "MBMU22/0553", Branch.CSE),
    Student("TEJAS BHATI", "29/09/2004", "23UFIE2272", "MBMU22/0236", Branch.CSE),
    Student("UDARAM", "26/01/2003", "23UFIE2279", "MBMU22/0237", Branch.CSE),
    Student("VAIBHAV BOSE", "8/9/2003", "23UFIE2286", "MBMU22/0554", Branch.CSE),
    Student("VIPASH MEENA", "2/2/2004", "23UFIE2310", "MBMU22/0238", Branch.CSE),
    Student("VISHWAS GAUR", "11/4/2002", "23UFIE2318", "MBMU22/0555", Branch.CSE),
    Student("YASHIKA GARG", "25/05/2004", "23UFIE2329", "MBMU22/0239", Branch.CSE),
]

# -----------------------------------------------------------------------------
# 5. ELECTRICAL ENGINEERING (EE) - 36 Students
# -----------------------------------------------------------------------------
EE_STUDENTS: List[Student] = [
    Student("AJAY JAJORIYA", "23/06/2007", "23UFIA1027", "MBMU22/0566", Branch.EE),
    Student("AMAN KUMAR MEENA", "7/5/2002", "23UFIA1036", "MBMU22/0569", Branch.EE),
    Student("AMBA BHEEL", "11/10/2003", "23UFIA1039", "MBMU22/0138", Branch.EE),
    Student("ANIRUDH SHARMA", "21/07/2004", "23UFIA1049", "MBMU22/0139", Branch.EE),
    Student("ANKIT JANGID", "8/11/2003", "23UFIA1058", "MBMU22/0140", Branch.EE),
    Student("ANSHUL AGRAWAL", "16/01/2004", "23UFIA1070", "MBMU22/0141", Branch.EE),
    Student("ARTI SAINI", "4/5/2003", "23UFIA1085", "MBMU22/0570", Branch.EE),
    Student("BHAWANSH VYAS", "21/09/2004", "23UFIA1122", "MBMU22/0142", Branch.EE),
    Student("BHUVNESH SAIN", "20/10/2005", "23UFIA1126", "MBMU22/0143", Branch.EE),
    Student("CHIRAG TIKWANI", "12/6/2004", "23UFIA1134", "MBMU22/0144", Branch.EE),
    Student("DEEKSHA BUG", "5/2/2003", "23UFIA1142", "MBMU22/0145", Branch.EE),
    Student("DEEKSHA MAHAVAR", "6/8/2004", "23UFIA1143", "MBMU22/0146", Branch.EE),
    Student("GOURAV", "18/04/2001", "23UFIA1194", "MBMU22/0571", Branch.EE),
    Student("HARISH SOOD", "3/3/2005", "23UFIA1201", "MBMU22/0147", Branch.EE),
    Student("JAGDISH MEENA", "19/08/2002", "23UFIA1239", "MBMU22/0148", Branch.EE),
    Student("JATIN JOSHI", "30/07/2005", "23UFIA1246", "MBMU22/0572", Branch.EE),
    Student("JIGYASA CHOUHAN", "4/10/2003", "23UFIA1254", "MBMU22/0510", Branch.EE),
    Student("JYOTI CHARAN", "26/06/2002", "23UFIA1256", "MBMU22/0149", Branch.EE),
    Student("KARAN VYAS", "18/02/2002", "23UFIA1264", "MBMU22/0490", Branch.EE),
    Student("KOMAL PRAJAPAT", "9/8/2005", "23UFIA1287", "MBMU22/0150", Branch.EE),
    Student("KULDEEP SINGH GURJAR", "24/06/2005", "23UFIA1298", "MBMU22/0151", Branch.EE),
    Student("MANISH JAKHAR", "20/10/2003", "23UFIA1333", "MBMU22/0152", Branch.EE),
    Student("MOHAMMAD YUNUS", "17/08/2003", "23UFIE2015", "MBMU22/0153", Branch.EE),
    Student("MONU", "26/03/2004", "23UFIE2025", "MBMU22/0154", Branch.EE),
    Student("PINKY KUMAWAT", "18/07/2004", "23UFIE2077", "MBMU22/0155", Branch.EE),
    Student("PRABHANJ DEV SHARMA", "11/8/2002", "23UFIE2085", "MBMU22/0156", Branch.EE),
    Student("RAHUL BRIJWAL", "5/8/2005", "23UFIE2121", "MBMU22/0157", Branch.EE),
    Student("SAMAKSH PAREEK", "11/7/2002", "23UFIE2188", "MBMU22/0158", Branch.EE),
    Student("SAURABH KHATRI", "10/9/2003", "23UFIE2206", "MBMU22/0505", Branch.EE),
    Student("SURENDRA CHOUDHARY", "8/10/2003", "23UFIE2256", "MBMU22/0159", Branch.EE),
    Student("TANMAY KHILAR", "30/03/2005", "23UFIE2265", "MBMU22/0160", Branch.EE),
    Student("TANU RAMAWAT", "17/01/2004", "23UFIE2267", "MBMU22/0161", Branch.EE),
    Student("TARUN BHATI", "12/6/2003", "23UFIE2269", "MBMU22/0162", Branch.EE),
    Student("YASH KAKKAR", "13/06/2003", "23UFIE2326", "MBMU22/0163", Branch.EE),
    Student("YASHITA KUMAWAT", "7/5/2004", "23UFIE2330", "MBMU22/0164", Branch.EE),
    Student("YASHWANT SINGH", "18/01/2006", "23UFIE2332", "MBMU22/0165", Branch.EE),
]

# -----------------------------------------------------------------------------
# 6. ELECTRONICS & COMMUNICATION ENGINEERING (ECE) - 24 Students
# -----------------------------------------------------------------------------
ECE_STUDENTS: List[Student] = [
    Student("ABHAY SHANKAR BOHRA", "30/06/2004", "23UFIA1011", "MBMU22/0103", Branch.ECE),
    Student("ANSH CHANDEL", "03/02/2004", "23UFIA1065", "MBMU22/0104", Branch.ECE),
    Student("ANSHUL PAREEK", "26/02/2004", "23UFIA1073", "MBMU22/0105", Branch.ECE),
    Student("ASHVANI KUMARI", "13/08/2004", "23UFIA1101", "MBMU22/0106", Branch.ECE),
    Student("CHETAN KUMAR MEENA", "18/08/2003", "23UFIA1132", "MBMU22/0107", Branch.ECE),
    Student("DEEPAK", "16/10/2004", "23UFIA1144", "MBMU22/0557", Branch.ECE, "deepak_ece"),
    Student("DIGVIJAY SINGH DEVRA", "05/06/2003", "23UFIA1161", "MBMU22/0558", Branch.ECE),
    Student("HARSH SHARMA", "15/05/2002", "23UFIA1204", "MBMU22/0108", Branch.ECE),
    Student("HARSH VARDHAN INDALIA", "19/01/2003", "23UFIA1205", "MBMU22/0501", Branch.ECE),
    Student("HARSHIT PUROHIT", "15/02/2003", "23UFIA1212", "MBMU22/0560", Branch.ECE),
    Student("HARSHIT SAINI", "18/01/2003", "23UFIA1213", "MBMU22/0109", Branch.ECE),
    Student("ISHAN MEENA", "30/10/2004", "23UFIA1235", "MBMU22/0110", Branch.ECE),
    Student("KISHAN LAL", "26/06/2003", "23UFIA1283", "MBMU22/0111", Branch.ECE),
    Student("KUMKUM SONI", "06/01/2004", "23UFIA1301", "MBMU22/0112", Branch.ECE),
    Student("LALIT KUMAR SUMAN", "29/05/2003", "23UFIA1311", "MBMU22/0563", Branch.ECE),
    Student("LAVI GARG", "09/09/2005", "23UFIA1313", "MBMU22/0113", Branch.ECE),
    Student("MONIKA MEENA", "07/03/2003", "23UFIE2023", "MBMU22/0114", Branch.ECE, "monika_meena_ece"),
    Student("NANDINI SONI", "03/09/2003", "23UFIE2040", "MBMU22/0115", Branch.ECE),
    Student("NIKITA SAINI", "18/04/2003", "23UFIE2057", "MBMU22/0116", Branch.ECE),
    Student("NIKITA YADAV", "14/07/2004", "23UFIE2058", "MBMU22/0117", Branch.ECE),
    Student("PRACHI SHARMA", "25/06/2004", "23UFIE2087", "MBMU22/0506", Branch.ECE),
    Student("RAGHAV PARASHAR", "03/04/2004", "23UFIE2117", "MBMU22/0118", Branch.ECE),
    Student("SAURABH JANGID", "03/03/2003", "23UFIE2205", "MBMU22/0119", Branch.ECE),
    Student("VIJAY LAXMI PAREEK", "01/10/2004", "23UFIE2300", "MBMU22/0120", Branch.ECE),
]

# -----------------------------------------------------------------------------
# 7. ELECTRONICS & COMPUTER ENGINEERING (ECC) - 36 Students
# -----------------------------------------------------------------------------
ECC_STUDENTS: List[Student] = [
    Student("ABHIJEET GOSWAMI", "24/04/2003", "23UFIA1012", "MBMU22/0243", Branch.ECC),
    Student("ABHISHEK CHOUDHARY", "21/02/2005", "23UFIA1016", "MBMU22/0520", Branch.ECC),
    Student("AMAN BATODIYA", "02/02/2004", "23UFIA1035", "MBMU22/0244", Branch.ECC),
    Student("ANJALI", "17/12/2002", "23UFIA1052", "MBMU22/0245", Branch.ECC),
    Student("ANSHUL KHANDELWAL", "02/07/2003", "23UFIA1072", "MBMU22/0246", Branch.ECC),
    Student("ARPIT SONI", "05/03/2005", "23UFIA1084", "MBMU22/0247", Branch.ECC),
    Student("ASHOK KUMAR BAIRWA", "01/07/2003", "23UFIA1100", "MBMU22/0538", Branch.ECC),
    Student("GOPAL VAISHNAV", "01/08/2004", "23UFIA1192", "MBMU22/0248", Branch.ECC),
    Student("GOURAB KUMAR SHUKLA", "25/06/2002", "23UFIA1193", "MBMU22/0527", Branch.ECC),
    Student("HIMANSHU SEEHRA", "25/05/2005", "23UFIA1227", "MBMU22/0249", Branch.ECC),
    Student("JALAJ TANWAR", "06/06/2004", "23UFIA1242", "MBMU22/0250", Branch.ECC),
    Student("JAYA KHATRI", "31/10/2003", "23UFIA1251", "MBMU22/0251", Branch.ECC),
    Student("KASHISH KUMAWAT", "25/07/2004", "23UFIA1269", "MBMU22/0252", Branch.ECC),
    Student("KHUSHDEEP PHOPHALIA", "26/12/2003", "23UFIA1276", "MBMU22/0253", Branch.ECC),
    Student("MAHAK BOHRA", "03/03/2005", "23UFIA1320", "MBMU22/0254", Branch.ECC),
    Student("MAHENDRA SINGH", "05/09/2004", "23UFIA1324", "MBMU22/0521", Branch.ECC),
    Student("MANISH POSWAL", "24/12/2002", "23UFIA1335", "MBMU22/0255", Branch.ECC),
    Student("MANISHA", "25/03/2003", "23UFIA1337", "MBMU22/0256", Branch.ECC, "manisha_ecc1"),
    Student("MANISHA", "11/02/2003", "23UFIA1338", "MBMU22/0257", Branch.ECC, "manisha_ecc2"),
    Student("MANU SHARMA", "31/01/2004", "23UFIA1347", "MBMU22/0258", Branch.ECC),
    Student("NAMAN KUMAWAT", "30/09/2003", "23UFIE2038", "MBMU22/0259", Branch.ECC),
    Student("PRIYANSHU DADHICH", "17/12/2004", "23UFIE2105", "MBMU22/0260", Branch.ECC),
    Student("PULKIT PURAKA", "23/07/2003", "23UFIE2109", "MBMU22/0261", Branch.ECC),
    Student("RAKESH KUMAR GOYAL", "25/12/2003", "23UFIE2135", "MBMU22/0262", Branch.ECC),
    Student("RAVI CHOUDHARY", "04/11/2004", "23UFIE2145", "MBMU22/0263", Branch.ECC),
    Student("RIDHIMA KHAJANCHI", "19/08/2004", "23UFIE2152", "MBMU22/0539", Branch.ECC),
    Student("RISHU SAIN", "25/09/2003", "23UFIE2161", "MBMU22/0264", Branch.ECC),
    Student("RIYA RAJPUROHIT", "25/04/2005", "23UFIE2167", "MBMU22/0265", Branch.ECC),
    Student("SANJAY KUMAR MEENA", "07/07/2004", "23UFIE2195", "MBMU22/0266", Branch.ECC),
    Student("SAREEF", "10/07/2002", "23UFIE2200", "MBMU22/0267", Branch.ECC),
    Student("SUJAL TIWARI", "01/01/2003", "23UFIE2244", "MBMU22/0268", Branch.ECC),
    Student("TEJKARAN CHOUDHARY", "12/12/2004", "23UFIE2274", "MBMU22/0269", Branch.ECC),
    Student("TEJSVI SHARMA", "15/12/2002", "23UFIE2275", "MBMU22/0270", Branch.ECC),
    Student("VIVEENA KHATRI", "04/10/2004", "23UFIE2319", "MBMU22/0365", Branch.ECC),
    Student("YASH DHANKAR", "15/12/2003", "23UFIE2324", "MBMU22/0271", Branch.ECC),
    Student("YUVRAJ SINGH MERTIA", "01/09/2003", "23UFIE2340", "MBMU22/0272", Branch.ECC),
]

# -----------------------------------------------------------------------------
# 8. ELECTRONICS & ELECTRICAL ENGINEERING (EEE) - 49 Students
# -----------------------------------------------------------------------------
EEE_STUDENTS: List[Student] = [
    Student("AAYUSH CHHAJER", "13/07/2004", "23UFIA1006", "MBMU22/0326", Branch.EEE),
    Student("ABHISHEK SINGH BHATI", "07/04/2004", "23UFIA1021", "MBMU22/0327", Branch.EEE),
    Student("ADITYA DAVE", "13/04/2004", "23UFIA1023", "MBMU22/0328", Branch.EEE),
    Student("AJAY SHARMA", "10/10/2003", "23UFIA1028", "MBMU22/0329", Branch.EEE),
    Student("AMAN SISODIA", "05/10/2004", "23UFIA1038", "MBMU22/0330", Branch.EEE),
    Student("AMIR KHAN", "05/03/2003", "23UFIA1040", "MBMU22/0331", Branch.EEE),
    Student("ANKIT KARODIYA", "15/07/2004", "23UFIA1059", "MBMU22/0528", Branch.EEE),
    Student("ARCHI GOYAL", "16/09/2003", "23UFIA1082", "MBMU22/0332", Branch.EEE),
    Student("ARYAN AKARNIYA", "03/10/2004", "23UFIA1089", "MBMU22/0333", Branch.EEE),
    Student("DIKSHA CHOUDHARY", "09/01/2004", "23UFIA1162", "MBMU22/0334", Branch.EEE),
    Student("DILEEP NAGAR", "30/08/2003", "23UFIA1165", "MBMU22/0335", Branch.EEE),
    Student("DIPTANSHU CHAUDHARY", "16/08/2004", "23UFIA1168", "MBMU22/0522", Branch.EEE),
    Student("EIJAZ AHMED", "13/03/2004", "23UFIA1179", "MBMU22/0336", Branch.EEE),
    Student("HARDIK SINGH RATHORE", "08/05/2003", "23UFIA1199", "MBMU22/0337", Branch.EEE),
    Student("HARSH SENGUPTA", "27/04/2004", "23UFIA1203", "MBMU22/0530", Branch.EEE),
    Student("HARSHIT MEENA", "13/08/2004", "23UFIA1208", "MBMU22/0338", Branch.EEE),
    Student("HARSHUL KACHHWAHA", "31/03/2004", "23UFIA1217", "MBMU22/0339", Branch.EEE),
    Student("JATIN SINGH RAJPUROHIT", "15/05/2002", "23UFIA1249", "MBMU22/0340", Branch.EEE),
    Student("JITENDRA VYAS", "19/02/2004", "23UFIA1255", "MBMU22/0341", Branch.EEE),
    Student("KHAWAHISH MATHUR", "07/03/2005", "23UFIA1274", "MBMU22/0343", Branch.EEE),
    Student("KOSHAL SARSWAT", "04/02/2004", "23UFIA1289", "MBMU22/0344", Branch.EEE),
    Student("KSHITIJ CHANDEL", "12/11/2004", "23UFIA1296", "MBMU22/0345", Branch.EEE),
    Student("LAVESH BHANSALI", "06/07/2004", "23UFIA1312", "MBMU22/0346", Branch.EEE),
    Student("LOKESH KUMAWAT", "15/08/2004", "23UFIA1316", "MBMU22/0347", Branch.EEE),
    Student("MADHURIMA RATHORE", "22/10/2003", "23UFIA1319", "MBMU22/0348", Branch.EEE),
    Student("MANVENDRA SHARMA", "11/10/2006", "23UFIE2002", "MBMU22/0497", Branch.EEE),
    Student("MOHIT KUMAR SAINI", "01/08/2005", "23UFIE2018", "MBMU22/0531", Branch.EEE),
    Student("MOHIT SONI", "05/07/2003", "23UFIE2021", "MBMU22/0349", Branch.EEE),
    Student("MONIKA", "10/12/2004", "23UFIE2022", "MBMU22/0350", Branch.EEE),
    Student("MRIGANK MEENA", "07/11/2004", "23UFIE2027", "MBMU22/0351", Branch.EEE),
    Student("MS. NIKITA GUPTA", "14/02/2004", "23UFIE2028", "MBMU22/0352", Branch.EEE),
    Student("PRIYANSH VYAS", "20/08/2004", "23UFIE2104", "MBMU22/0353", Branch.EEE),
    Student("RAGHAV DADHICH", "12/04/2003", "23UFIE2115", "MBMU22/0354", Branch.EEE),
    Student("RAMANSHI DADHEECH", "13/02/2004", "23UFIE2138", "MBMU22/0355", Branch.EEE),
    Student("RITIK SOTWAL", "19/12/2003", "23UFIE2163", "MBMU22/0356", Branch.EEE),
    Student("RIYA GUPTA", "19/10/2003", "23UFIE2165", "MBMU22/0357", Branch.EEE),
    Student("RIYA JAKHAR", "04/08/2003", "23UFIE2166", "MBMU22/0358", Branch.EEE),
    Student("ROHIT KUMAR", "21/07/2003", "23UFIE2172", "MBMU22/0532", Branch.EEE),
    Student("SACHIN CHOUDHARY", "01/03/2004", "23UFIE2182", "MBMU22/0359", Branch.EEE),
    Student("SANIYA BALUNDIYA", "07/07/2004", "23UFIE2191", "MBMU22/0360", Branch.EEE),
    Student("SARIKA MEENA", "18/01/2004", "23UFIE2201", "MBMU22/0533", Branch.EEE),
    Student("SHYAM SUNDAR SHARMA", "24/05/2003", "23UFIE2222", "MBMU22/0367", Branch.EEE),
    Student("SUDARSHAN CHAUHAN", "29/01/2005", "23UFIE2241", "MBMU22/0361", Branch.EEE),
    Student("VEDANT DRONA", "20/07/2004", "23UFIE2294", "MBMU22/0362", Branch.EEE),
    Student("VIDHI DAVE", "21/01/2005", "23UFIE2298", "MBMU22/0535", Branch.EEE),
    Student("VIRAT PANDEY", "24/04/2003", "23UFIE2311", "MBMU22/0363", Branch.EEE),
    Student("VISHAL KUMAR MEENA", "16/01/2003", "23UFIE2315", "MBMU22/0364", Branch.EEE),
    Student("YASH MAHRIA", "06/06/2004", "23UFIE2327", "MBMU22/0366", Branch.EEE),
    Student("YUVRAJ SINGH RATHORE", "20/04/2004", "23UFIE2341", "MBMU22/0534", Branch.EEE),
]

# -----------------------------------------------------------------------------
# 9. INFORMATION TECHNOLOGY (IT) - 25 Students
# -----------------------------------------------------------------------------
IT_STUDENTS: List[Student] = [
    Student("ABHISHEK JANGIR", "31/10/2003", "23UFIA1019", "MBMU22/0121", Branch.IT),
    Student("AKSHAY KUMAR GUPTA", "19/04/2002", "23UFIA1032", "MBMU22/0561", Branch.IT),
    Student("AKSHIT GANG", "16/08/2004", "23UFIA1033", "MBMU22/0304", Branch.IT),
    Student("ANSHUL JANGID", "25/07/2003", "23UFIA1071", "MBMU22/0122", Branch.IT),
    Student("ARUN NAIN", "26/06/2002", "23UFIA1087", "MBMU22/0123", Branch.IT),
    Student("ARYAN PARASHAR", "24/07/2003", "23UFIA1091", "MBMU22/0562", Branch.IT),
    Student("ARYAN SHARMA", "27/09/2003", "23UFIA1092", "MBMU22/0517", Branch.IT),
    Student("ASHISH KUMAR YADAV", "05/03/2005", "23UFIA1097", "MBMU22/0124", Branch.IT),
    Student("HANSIKA SIGGAR", "12/09/2004", "23UFIA1197", "MBMU22/0125", Branch.IT),
    Student("JATIN AGARWAL", "28/02/2003", "23UFIA1245", "MBMU22/0126", Branch.IT),
    Student("KANAK CHOUHAN", "13/03/2003", "23UFIA1259", "MBMU22/0127", Branch.IT),
    Student("MEGHA ROPIA", "24/09/2003", "23UFIE2011", "MBMU22/0128", Branch.IT),
    Student("MRIDUL BANSAL", "12/08/2003", "23UFIE2026", "MBMU22/0568", Branch.IT),
    Student("PARTH SHARMA", "07/09/2004", "23UFIE2069", "MBMU22/0129", Branch.IT),
    Student("PRATEEK DAVE", "17/05/2004", "23UFIE2091", "MBMU22/0130", Branch.IT),
    Student("PRIYAM KUMAR", "17/06/2003", "23UFIE2101", "MBMU22/0131", Branch.IT),
    Student("ROHIT YADAV", "06/02/2005", "23UFIE2176", "MBMU22/0567", Branch.IT),
    Student("SATVIK AGRAWAL", "23/09/2002", "23UFIE2203", "MBMU22/0498", Branch.IT),
    Student("SUDHANSHU BHARGAVA", "23/05/2003", "23UFIE2243", "MBMU22/0132", Branch.IT),
    Student("SUMIT BORAWAT", "22/02/2004", "23UFIE2246", "MBMU22/0133", Branch.IT),
    Student("SWAPNIL", "27/11/2002", "23UFIE2258", "MBMU22/0565", Branch.IT),
    Student("TANMAY JAIN", "06/01/2003", "23UFIE2262", "MBMU22/0134", Branch.IT),
    Student("TAPISH SODANI", "10/12/2004", "23UFIE2268", "MBMU22/0135", Branch.IT),
    Student("YOGENDER GODARA", "01/07/2004", "23UFIE2333", "MBMU22/0136", Branch.IT),
    Student("YUKTA MEENA", "12/07/2003", "23UFIE2335", "MBMU22/0137", Branch.IT),
]

# -----------------------------------------------------------------------------
# 10. MECHANICAL ENGINEERING (ME) - 41 Students
# -----------------------------------------------------------------------------
ME_STUDENTS: List[Student] = [
    Student("ABHISHEK DUDI", "03/01/2003", "23UFIA1018", "MBMU22/0410", Branch.ME),
    Student("AKSHIT MEENA", "07/12/2003", "23UFIA1034", "MBMU22/0411", Branch.ME),
    Student("ANKIT KUMAR SAINI", "05/01/2003", "23UFIA1061", "MBMU22/0412", Branch.ME),
    Student("ANKITA GOUR", "12/01/2007", "23UFIA1064", "MBMU22/0574", Branch.ME),
    Student("ARYAN", "20/10/2003", "23UFIA1088", "MBMU22/0413", Branch.ME, "aryan_me"),
    Student("ARYAN SINGH", "10/01/2004", "23UFIA1093", "MBMU22/0414", Branch.ME),
    Student("AVINASH MEENA", "25/05/2005", "23UFIA1103", "MBMU22/0415", Branch.ME),
    Student("BANSHIDHAR BHOBARIYA", "28/11/2005", "23UFIA1110", "MBMU22/0509", Branch.ME),
    Student("BHANU PRATAP SINGH", "25/12/2003", "23UFIA1111", "MBMU22/0416", Branch.ME),
    Student("CHANDERPAL SINGH", "11/10/2003", "23UFIA1130", "MBMU22/0417", Branch.ME),
    Student("DARSHAN RANA", "06/11/2004", "23UFIA1138", "MBMU22/0418", Branch.ME),
    Student("DINESH CHOUHAN", "21/11/2004", "23UFIA1167", "MBMU22/0516", Branch.ME),
    Student("DIVYA JANGID", "09/04/2005", "23UFIA1169", "MBMU22/0419", Branch.ME),
    Student("DUSHYANT GEHLOT", "20/06/2004", "23UFIA1178", "MBMU22/0420", Branch.ME),
    Student("GAJENDRA SINGH RAJPUROHIT", "05/03/2005", "23UFIA1180", "MBMU22/0421", Branch.ME),
    Student("HARSHIT MEENA", "17/06/2004", "23UFIA1209", "MBMU22/0422", Branch.ME, "harshit_meena_me"),
    Student("KISHOR", "01/01/2004", "23UFIA1284", "MBMU22/0423", Branch.ME),
    Student("LOVJEET PARIHAR", "08/03/2003", "23UFIA1317", "MBMU22/0424", Branch.ME),
    Student("MAHAVEER SONI", "04/01/2005", "23UFIA1321", "MBMU22/0425", Branch.ME),
    Student("MAYA SHARMA", "26/01/2004", "23UFIE2006", "MBMU22/0426", Branch.ME),
    Student("MOHIT JHALA", "21/07/2004", "23UFIE2017", "MBMU22/0427", Branch.ME),
    Student("MOHIT SANKHLA", "11/01/2004", "23UFIE2020", "MBMU22/0428", Branch.ME),
    Student("NANDINI RAJPUROHIT", "15/09/2003", "23UFIE2039", "MBMU22/0429", Branch.ME),
    Student("PAWAN GURJAR", "05/09/2003", "23UFIE2071", "MBMU22/0430", Branch.ME),
    Student("PRASHANT AMERIYA", "12/08/2003", "23UFIE2089", "MBMU22/0431", Branch.ME),
    Student("RAHUL SUWALKA", "08/08/2003", "23UFIE2126", "MBMU22/0511", Branch.ME),
    Student("RAJAT GUPTA", "04/05/2004", "23UFIE2130", "MBMU22/0432", Branch.ME),
    Student("RAKESH DHOLI", "12/01/2004", "23UFIE2134", "MBMU22/0433", Branch.ME),
    Student("SACHIN JAKHAR", "23/06/2004", "23UFIE2183", "MBMU22/0434", Branch.ME),
    Student("SAMEER KUMAR", "26/05/2005", "23UFIE2189", "MBMU22/0512", Branch.ME),
    Student("SANJAY ASERI", "17/10/2002", "23UFIE2193", "MBMU22/0435", Branch.ME),
    Student("SATISH PARMAR", "15/05/2004", "23UFIE2202", "MBMU22/0436", Branch.ME),
    Student("SHREE MITTAL", "19/01/2004", "23UFIE2214", "MBMU22/0437", Branch.ME),
    Student("SUNIL KUMAR BIJARNIYA", "15/01/2004", "23UFIE2248", "MBMU22/0513", Branch.ME),
    Student("SUNIL KUMAR MEENA", "25/04/2006", "23UFIE2249", "MBMU22/0438", Branch.ME),
    Student("SURAJ AJAR", "05/07/2001", "23UFIE2253", "MBMU22/0439", Branch.ME),
    Student("SURAJ BHADANIA", "10/09/2003", "23UFIE2254", "MBMU22/0514", Branch.ME),
    Student("VIDUSHI RATHORE", "15/12/2003", "23UFIE2299", "MBMU22/0440", Branch.ME),
    Student("VISHAKHA GAUTAM", "02/09/2003", "23UFIE2312", "MBMU22/0441", Branch.ME),
    Student("VIVEK KUMAR", "28/02/2004", "23UFIE2321", "MBMU22/0442", Branch.ME),
    Student("YUVRAJ SINGH", "21/10/2003", "23UFIE2336", "MBMU22/0443", Branch.ME, "yuvraj_singh_me"),
]

# -----------------------------------------------------------------------------
# 11. MINING ENGINEERING - 35 Students
# -----------------------------------------------------------------------------
MINING_STUDENTS: List[Student] = [
    Student("ABDUL MALIK", "07/04/2001", "23UFIA1009", "MBMU22/0273", Branch.MINING),
    Student("AMRIT KALBI", "29/06/2005", "23UFIA1042", "MBMU22/0542", Branch.MINING),
    Student("ANUJA SHARMA", "29/08/2003", "23UFIA1078", "MBMU22/0274", Branch.MINING),
    Student("AYUSH SHARMA", "22/09/2003", "23UFIA1107", "MBMU22/0275", Branch.MINING),
    Student("BHAVYANSH GUND", "25/12/2003", "23UFIA1119", "MBMU22/0276", Branch.MINING),
    Student("DEVANSH SHARMA", "04/08/2004", "23UFIA1150", "MBMU22/0277", Branch.MINING),
    Student("DIVYANSHU", "20/11/2003", "23UFIA1174", "MBMU22/0278", Branch.MINING),
    Student("HEMANGI SUKHADIYA", "24/05/2005", "23UFIA1220", "MBMU22/0279", Branch.MINING),
    Student("HIMANSHU AMBESH", "22/02/2004", "23UFIA1224", "MBMU22/0280", Branch.MINING),
    Student("KANAK UJJENIYA", "10/05/2004", "23UFIA1260", "MBMU22/0281", Branch.MINING),
    Student("MANEESH KUMAR", "28/04/2003", "23UFIA1332", "MBMU22/0282", Branch.MINING),
    Student("MS. PRATIKSHA SINGHAL", "20/09/2005", "23UFIE2029", "MBMU22/0283", Branch.MINING),
    Student("MUKESH KUMAR KOK", "08/05/2004", "23UFIE2035", "MBMU22/0284", Branch.MINING),
    Student("NITU", "10/06/2005", "23UFIE2062", "MBMU22/0285", Branch.MINING),
    Student("PINKI KHARRA", "07/02/2004", "23UFIE2076", "MBMU22/0286", Branch.MINING),
    Student("PIYUSH NAVAL", "17/12/2002", "23UFIE2079", "MBMU22/0287", Branch.MINING),
    Student("POOJA CHOUDHARY", "12/07/2003", "23UFIE2083", "MBMU22/0288", Branch.MINING),
    Student("PRADEEP", "25/02/2005", "23UFIE2088", "MBMU22/0289", Branch.MINING),
    Student("PRATEEK LAMBA", "24/07/2004", "23UFIE2092", "MBMU22/0290", Branch.MINING),
    Student("RAJVARDHAN SINGH RATHORE", "09/02/2004", "23UFIE2132", "MBMU22/0291", Branch.MINING),
    Student("RAM LAKHAN", "31/12/2003", "23UFIE2137", "MBMU22/0292", Branch.MINING),
    Student("RAMKISHORE", "15/07/2004", "23UFIE2140", "MBMU22/0293", Branch.MINING),
    Student("RATAN YADAV", "09/07/2003", "23UFIE2144", "MBMU22/0294", Branch.MINING),
    Student("ROHIT YADAV", "11/04/2004", "23UFIE2177", "MBMU22/0295", Branch.MINING, "rohit_yadav_mining"),
    Student("SONU MEENA", "28/04/2004", "23UFIE2237", "MBMU22/0296", Branch.MINING, "sonu_meena_mining1"),
    Student("SONU MEENA", "16/09/2005", "23UFIE2238", "MBMU22/0297", Branch.MINING, "sonu_meena_mining2"),
    Student("TOSHIKA BAWANKAR", "29/03/2005", "23UFIE2277", "MBMU22/0500", Branch.MINING),
    Student("VAIBHAV SONI", "04/10/2006", "23UFIE2288", "MBMU22/0298", Branch.MINING),
    Student("VANSH CHOUHAN", "15/05/2003", "23UFIE2289", "MBMU22/0299", Branch.MINING),
    Student("VISHWAM PAREEK", "09/12/2003", "23UFIE2317", "MBMU22/0300", Branch.MINING),
    Student("VIVEK GARG", "27/11/2004", "23UFIE2320", "MBMU22/0301", Branch.MINING),
    Student("YOGESH KUMAWAT", "14/08/2004", "23UFIE2334", "MBMU22/0302", Branch.MINING),
    Student("MAYANK CHOUDHARY", "12/07/2003", "23UFIE2007", "MBMU22/0499", Branch.MINING),
    Student("SAURABH GURNANI", "20/06/2003", "23UFIE2204", "MBMU22/0507", Branch.MINING),
    Student("ISHIKA PRAJAPATI", "10/02/2004", "23UFIA1237", "MBMU22/0489", Branch.MINING),
]

# -----------------------------------------------------------------------------
# 12. PETROLEUM ENGINEERING - 38 Students
# -----------------------------------------------------------------------------
PETROLEUM_STUDENTS: List[Student] = [
    Student("AAYUSH CHOUDHARY", "01/01/2004", "23UFIA1007", "MBMU22/0183", Branch.PETROLEUM),
    Student("ABHISHEK SINGH", "22/11/2004", "23UFIA1020", "MBMU22/0184", Branch.PETROLEUM),
    Student("ANJALI JODHA", "17/09/2003", "23UFIA1053", "MBMU22/0573", Branch.PETROLEUM),
    Student("ANSH JINDAL", "04/04/2004", "23UFIA1066", "MBMU22/0185", Branch.PETROLEUM),
    Student("ARUN KARWASARA", "07/11/2003", "23UFIA1086", "MBMU22/0186", Branch.PETROLEUM),
    Student("ASHOK BHARTI GOSWAMI", "15/04/2002", "23UFIA1099", "MBMU22/0187", Branch.PETROLEUM),
    Student("BHUMIKA RANAWAT", "15/03/2005", "23UFIA1125", "MBMU22/0188", Branch.PETROLEUM),
    Student("CHANCHAL SHARMA", "13/06/2004", "23UFIA1129", "MBMU22/0189", Branch.PETROLEUM),
    Student("DEEPAK PRAJAPAT", "30/07/2003", "23UFIA1147", "MBMU22/0556", Branch.PETROLEUM),
    Student("DHARMENDRA SENWAR", "27/04/2003", "23UFIA1153", "MBMU22/0190", Branch.PETROLEUM),
    Student("JANAK BORAWAR", "17/03/2004", "23UFIA1243", "MBMU22/0191", Branch.PETROLEUM),
    Student("JATIN KUMAR", "11/08/2004", "23UFIA1247", "MBMU22/0192", Branch.PETROLEUM),
    Student("KARTIK", "12/12/2003", "23UFIA1265", "MBMU22/0193", Branch.PETROLEUM, "kartik_petro"),
    Student("KESHAV BORA", "17/11/2004", "23UFIA1271", "MBMU22/0194", Branch.PETROLEUM),
    Student("KHUSHAL BOHRA", "30/09/2004", "23UFIA1275", "MBMU22/0195", Branch.PETROLEUM),
    Student("KHUSHI AGARWAL", "04/12/2003", "23UFIA1278", "MBMU22/0196", Branch.PETROLEUM),
    Student("KHUSHWANT JAKHAR", "07/07/2004", "23UFIA1280", "MBMU22/0197", Branch.PETROLEUM),
    Student("KRITIKA", "18/06/2004", "23UFIA1295", "MBMU22/0198", Branch.PETROLEUM),
    Student("KRITI VYAS", "26/12/2004", "23UFIA1294", "MBMU22/0579", Branch.PETROLEUM),
    Student("MAHENDRA", "02/08/2004", "23UFIA1322", "MBMU22/0199", Branch.PETROLEUM),
    Student("MANANT SHARMA", "19/11/2003", "23UFIA1329", "MBMU22/0200", Branch.PETROLEUM),
    Student("MANJU BISHNOI", "27/09/2004", "23UFIA1342", "MBMU22/0201", Branch.PETROLEUM),
    Student("MANOJ SANKHLA", "12/01/2004", "23UFIA1346", "MBMU22/0202", Branch.PETROLEUM),
    Student("MUKESH DEORA", "27/02/2002", "23UFIE2033", "MBMU22/0203", Branch.PETROLEUM),
    Student("PARTH SARTHI GOUR", "05/04/2004", "23UFIE2068", "MBMU22/0204", Branch.PETROLEUM),
    Student("PARTH VAISHNAV", "30/05/2004", "23UFIE2070", "MBMU22/0205", Branch.PETROLEUM),
    Student("PRERNA MEWARA", "10/06/2003", "23UFIE2097", "MBMU22/0206", Branch.PETROLEUM),
    Student("PUKHRAJ CHOUDHARY", "14/07/2005", "23UFIE2108", "MBMU22/0207", Branch.PETROLEUM),
    Student("RADHIKA SHARMA", "21/05/2005", "23UFIE2113", "MBMU22/0208", Branch.PETROLEUM),
    Student("RAVISH GOUR", "18/08/2004", "23UFIE2149", "MBMU22/0209", Branch.PETROLEUM),
    Student("SHUBHAM ROYAL", "13/07/2004", "23UFIE2219", "MBMU22/0210", Branch.PETROLEUM),
    Student("VINITA TIGAYA", "12/07/2004", "23UFIE2307", "MBMU22/0211", Branch.PETROLEUM),
    Student("VINOD GARG", "08/07/2003", "23UFIE2309", "MBMU22/0212", Branch.PETROLEUM),
    Student("NEHA PRAJAPAT", "22/05/2003", "23UFIE2048", "MBMU22/0577", Branch.PETROLEUM),
    Student("RAHUL KUMAR", "05/08/2003", "23UFIE2123", "MBMU22/0578", Branch.PETROLEUM),
    Student("SHYAM LAL", "30/06/2006", "23UFIE2221", "MBMU22/0580", Branch.PETROLEUM),
    Student("LAKSHIT GEHLOT", "06/08/2004", "23UFIA1307", "MBMU22/0575", Branch.PETROLEUM),
    Student("MOHD KASHIF", "15/04/2004", "23UFIE2016", "MBMU22/0576", Branch.PETROLEUM),
]

# -----------------------------------------------------------------------------
# 13. PRODUCTION & INDUSTRIAL ENGINEERING (PIE) - 16 Students
# -----------------------------------------------------------------------------
PIE_STUDENTS: List[Student] = [
    Student("ANIL", "21/03/2006", "23UFIA1046", "MBMU22/0368", Branch.PIE),
    Student("ANIRUDH RANGA", "17/09/2003", "23UFIA1048", "MBMU22/0369", Branch.PIE),
    Student("ANISHA BHATI", "13/06/2004", "23UFIA1051", "MBMU22/0370", Branch.PIE),
    Student("ANUJ GANDHI", "1/6/2003", "23UFIA1076", "MBMU22/0371", Branch.PIE),
    Student("BHAWANSH MATHUR", "30/07/2004", "23UFIA1121", "MBMU22/0372", Branch.PIE),
    Student("HITESH PARIHAR", "16/04/2003", "23UFIA1230", "MBMU22/0373", Branch.PIE),
    Student("KARTIK", "4/2/2004", "23UFIA1266", "MBMU22/0374", Branch.PIE, "kartik_pie"),
    Student("KRISHNA GODARA", "19/12/2004", "23UFIA1292", "MBMU22/0375", Branch.PIE),
    Student("LAXMI RATHORE", "13/06/2004", "23UFIA1315", "MBMU22/0376", Branch.PIE),
    Student("MANISHA CHOUDHARY", "6/7/2005", "23UFIA1339", "MBMU22/0377", Branch.PIE),
    Student("MAYANK MANTRI", "23/12/2003", "23UFIE2009", "MBMU22/0378", Branch.PIE),
    Student("MITHLESH SAINI", "2/4/2005", "23UFIE2013", "MBMU22/0379", Branch.PIE),
    Student("PAWAN RATHI", "18/12/2004", "23UFIE2074", "MBMU22/0380", Branch.PIE),
    Student("RAVINDRA KUMAR SAINI", "25/06/2005", "23UFIE2148", "MBMU22/0381", Branch.PIE),
    Student("SOUMYA ARORA", "23/01/2004", "23UFIE2225", "MBMU22/0382", Branch.PIE),
    Student("HIMANI RAWLOT", "18/07/2005", "23UFIA1221", "MBMU22/0508", Branch.PIE),
]


# =============================================================================
# STUDENT REGISTRY - All students combined
# =============================================================================

def get_all_students() -> List[Student]:
    """Get all students from all branches."""
    return (
        AI_DS_STUDENTS +
        CHEMICAL_STUDENTS +
        CIVIL_STUDENTS +
        CSE_STUDENTS +
        EE_STUDENTS +
        ECE_STUDENTS +
        ECC_STUDENTS +
        EEE_STUDENTS +
        IT_STUDENTS +
        ME_STUDENTS +
        MINING_STUDENTS +
        PETROLEUM_STUDENTS +
        PIE_STUDENTS
    )


def get_students_by_branch(branch: Branch) -> List[Student]:
    """Get all students for a specific branch."""
    branch_map = {
        Branch.AI_DS: AI_DS_STUDENTS,
        Branch.CHEMICAL: CHEMICAL_STUDENTS,
        Branch.CIVIL: CIVIL_STUDENTS,
        Branch.CSE: CSE_STUDENTS,
        Branch.EE: EE_STUDENTS,
        Branch.ECE: ECE_STUDENTS,
        Branch.ECC: ECC_STUDENTS,
        Branch.EEE: EEE_STUDENTS,
        Branch.IT: IT_STUDENTS,
        Branch.ME: ME_STUDENTS,
        Branch.MINING: MINING_STUDENTS,
        Branch.PETROLEUM: PETROLEUM_STUDENTS,
        Branch.PIE: PIE_STUDENTS,
    }
    return branch_map.get(branch, [])


def get_student_by_identifier(identifier: str) -> Optional[Student]:
    """Find student by their CLI identifier."""
    identifier = identifier.lower().strip()
    for student in get_all_students():
        if student.identifier == identifier:
            return student
    return None


def get_student_by_name(name: str) -> List[Student]:
    """Find students by name (may return multiple for common names)."""
    name = name.lower().strip()
    results = []
    for student in get_all_students():
        if name in student.name.lower():
            results.append(student)
    return results


def build_identifier_map() -> Dict[str, Student]:
    """Build a mapping of identifiers to students."""
    identifier_map = {}
    all_students = get_all_students()
    
    # First pass - count duplicates
    name_counts: Dict[str, int] = {}
    for student in all_students:
        base_id = student.identifier
        if base_id in name_counts:
            name_counts[base_id] += 1
        else:
            name_counts[base_id] = 1
    
    # Second pass - assign unique identifiers where needed
    name_seen: Dict[str, int] = {}
    for student in all_students:
        base_id = student.identifier
        
        if name_counts[base_id] > 1 and not any(c.isdigit() or c == '_' for c in base_id[-5:]):
            # Duplicate name - add suffix if not already unique
            if base_id in name_seen:
                name_seen[base_id] += 1
                unique_id = f"{base_id}_{name_seen[base_id]}"
            else:
                name_seen[base_id] = 1
                unique_id = base_id
            
            # Update student's identifier
            student.identifier = unique_id
            identifier_map[unique_id] = student
        else:
            identifier_map[base_id] = student
    
    return identifier_map


# Build the map on module load
STUDENT_MAP = build_identifier_map()


def get_all_identifiers() -> List[str]:
    """Get all unique student identifiers."""
    return list(STUDENT_MAP.keys())


# Branch summary
BRANCH_SUMMARY = {
    Branch.AI_DS: len(AI_DS_STUDENTS),
    Branch.CHEMICAL: len(CHEMICAL_STUDENTS),
    Branch.CIVIL: len(CIVIL_STUDENTS),
    Branch.CSE: len(CSE_STUDENTS),
    Branch.EE: len(EE_STUDENTS),
    Branch.ECE: len(ECE_STUDENTS),
    Branch.ECC: len(ECC_STUDENTS),
    Branch.EEE: len(EEE_STUDENTS),
    Branch.IT: len(IT_STUDENTS),
    Branch.ME: len(ME_STUDENTS),
    Branch.MINING: len(MINING_STUDENTS),
    Branch.PETROLEUM: len(PETROLEUM_STUDENTS),
    Branch.PIE: len(PIE_STUDENTS),
}

TOTAL_STUDENTS = sum(BRANCH_SUMMARY.values())
