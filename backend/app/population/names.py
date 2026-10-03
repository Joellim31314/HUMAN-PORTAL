"""Small deterministic first/last name pools keyed by cultural group."""
from __future__ import annotations

import numpy as np

FIRST = {
    "british": (
        ["Emily", "Charlotte", "Sophie", "Olivia", "Hannah", "Lucy", "Rebecca", "Katie", "Jessica", "Laura", "Amy", "Rachel", "Helen", "Claire", "Sarah", "Fiona", "Susan", "Margaret", "Jean", "Barbara"],
        ["James", "Oliver", "Harry", "Jack", "Thomas", "George", "Daniel", "Matthew", "Luke", "Ben", "Callum", "Ryan", "Andrew", "Mark", "Paul", "Peter", "David", "Michael", "Graham", "Keith"]),
    "other_white": (
        ["Anna", "Maria", "Agnieszka", "Elena", "Sofia", "Katarzyna", "Ioana", "Giulia", "Camille", "Marta", "Natalia", "Ewa"],
        ["Piotr", "Marek", "Andrei", "Luca", "Mateusz", "Pierre", "Jakub", "Stefan", "Marco", "Tomasz", "Dmitri", "Carlos"]),
    "bangladeshi": (
        ["Fatima", "Ayesha", "Nasrin", "Sadia", "Rahima", "Jannat", "Mariam", "Shirin", "Tasnim", "Rukhsana"],
        ["Mohammed", "Abdul", "Rahim", "Tariq", "Hasan", "Ismail", "Shamim", "Jamal", "Rafiq", "Faisal"]),
    "pakistani": (
        ["Aisha", "Zainab", "Hira", "Sana", "Amina", "Noor", "Saima", "Khadija", "Iqra", "Bushra"],
        ["Ahmed", "Usman", "Bilal", "Imran", "Hamza", "Zahid", "Asif", "Omar", "Adnan", "Kamran"]),
    "indian": (
        ["Priya", "Anjali", "Neha", "Divya", "Pooja", "Kavita", "Sunita", "Meera", "Ritu", "Anita"],
        ["Raj", "Amit", "Vikram", "Rohan", "Sanjay", "Arjun", "Nikhil", "Anil", "Suresh", "Kiran"]),
    "sikh": (
        ["Harpreet", "Gurpreet", "Manpreet", "Simran", "Jasleen", "Navneet"],
        ["Jaspal", "Harjit", "Balwinder", "Gurdeep", "Amarjit", "Ravinder"]),
    "chinese": (
        ["Mei", "Li", "Xin", "Yan", "Jing", "Wen", "Hui", "Ling"],
        ["Wei", "Jun", "Ming", "Chen", "Hao", "Jian", "Kai", "Lei"]),
    "other_asian": (
        ["Thi", "Lakshmi", "Nirmala", "Aiko", "Mai", "Sumi", "Hana", "Dewi"],
        ["Minh", "Kenji", "Ravi", "Anh", "Tuan", "Hiro", "Sunil", "Arif"]),
    "african": (
        ["Grace", "Blessing", "Adaeze", "Ngozi", "Abena", "Funmi", "Amara", "Esther", "Chidinma", "Folake"],
        ["Emmanuel", "Chinedu", "Kwame", "Olu", "Tunde", "Samuel", "Kofi", "Segun", "Ibrahim", "Yusuf"]),
    "caribbean": (
        ["Keisha", "Shanice", "Marcia", "Tamika", "Joy", "Paulette", "Aaliyah", "Denise"],
        ["Marcus", "Jermaine", "Winston", "Devon", "Leroy", "Trevor", "Dwayne", "Andre"]),
    "arab": (
        ["Layla", "Yasmin", "Rania", "Huda", "Salma", "Dina"],
        ["Khaled", "Youssef", "Ali", "Hassan", "Karim", "Samir"]),
    "other": (
        ["Mina", "Leila", "Sara", "Nadia", "Elif", "Roya", "Alicia", "Camila"],
        ["Reza", "Kemal", "Ali", "Javier", "Mehmet", "Diego", "Arman", "Joao"]),
}

LAST = {
    "british": ["Smith", "Jones", "Taylor", "Brown", "Williams", "Wilson", "Evans", "Thomas", "Roberts", "Walker", "Wright", "Robinson", "Thompson", "White", "Hughes", "Edwards", "Green", "Hall", "Wood", "Harris", "Clarke", "Turner", "Cooper", "Hill", "Ward"],
    "other_white": ["Kowalski", "Nowak", "Popescu", "Rossi", "Ivanov", "Dubois", "Garcia", "Silva", "Novak", "Petrov", "Costa", "Muller"],
    "bangladeshi": ["Rahman", "Uddin", "Ahmed", "Begum", "Khan", "Hossain", "Islam", "Miah", "Ali", "Chowdhury", "Akter", "Khatun"],
    "pakistani": ["Khan", "Hussain", "Malik", "Iqbal", "Butt", "Chaudhry", "Shah", "Mahmood", "Akhtar", "Sheikh"],
    "indian": ["Patel", "Shah", "Sharma", "Mehta", "Gupta", "Desai", "Joshi", "Nair", "Reddy", "Kapoor", "Verma", "Iyer"],
    "sikh": ["Singh", "Kaur", "Gill", "Dhillon", "Sandhu", "Sidhu", "Bains", "Grewal"],
    "chinese": ["Wong", "Chan", "Li", "Wang", "Zhang", "Liu", "Chen", "Lam", "Cheung", "Ng"],
    "other_asian": ["Nguyen", "Tran", "Tanaka", "Kim", "Park", "Santos", "Perera", "Fernando", "Lim", "Tan"],
    "african": ["Okafor", "Adeyemi", "Mensah", "Osei", "Okeke", "Abiodun", "Nwosu", "Mwangi", "Bello", "Owusu", "Adebayo", "Mohamud"],
    "caribbean": ["Campbell", "Brown", "Williams", "Clarke", "Henry", "Grant", "Morgan", "Reid", "Gordon", "Bailey"],
    "arab": ["Haddad", "Mansour", "Nasser", "Saleh", "Farouk", "Khoury"],
    "other": ["Yilmaz", "Demir", "Rezaei", "Hosseini", "Lopez", "Fernandez", "Pereira", "Karimi"],
}


def name_key(group: str, detail: str, religion: str, rng: np.random.Generator) -> str:
    if group == "White":
        return "other_white" if detail == "Other White" else "british"
    if group == "Asian":
        if detail == "Indian":
            return "sikh" if religion == "Sikh" else ("pakistani" if religion == "Muslim" else "indian")
        return {"Bangladeshi": "bangladeshi", "Pakistani": "pakistani", "Chinese": "chinese"}.get(detail, "other_asian")
    if group == "Black":
        return "caribbean" if detail == "Caribbean" else "african"
    if group == "Mixed":
        return str(rng.choice(["british", "british", "caribbean", "african", "indian"]))
    return "arab" if detail == "Arab" else "other"


def make_name(group: str, detail: str, religion: str, sex: str, rng: np.random.Generator) -> str:
    k = name_key(group, detail, religion, rng)
    first = FIRST[k][0 if sex == "female" else 1]
    return f"{rng.choice(first)} {rng.choice(LAST[k])}"
