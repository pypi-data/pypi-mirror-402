"""

This python package offers various visualization and web interface tools for calculus, chemistry, and data science,
with optional localization for the currently available language codes: ENG, FRA, SPA, KOR, and JPN.

This python package is primarily created for the stabilization and support of the current Softhauz system.

Author: Urate, Karen
Creation Date: 2025-12-01

"""

import datetime
import time
import uuid
import random

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import sympy
import base64

from chempy import balance_stoichiometry
from faker import Faker
from fractions import Fraction
from io import BytesIO
from math import gcd

from sympy import cos, diff, expand, idiff, integrate, lambdify, latex, limit, log, oo, parse_expr, pi, simplify, sin, solve, sqrt, symbols, sympify
from sympy import S, Function, Eq, Derivative, Integral, E, I
from sympy.calculus.util import continuous_domain
from sympy.plotting import plot

"""

This class is a collection of most commonly-used symbols and entities
for ease of accessibility and usage for expressions in a single instance. 

Author: Urate, Karen
Creation Date: 2025-12-01

"""
class Notations:

    ninf = S.NegativeInfinity
    inf = S.Infinity
    x = symbols('x', real=True)
    y = symbols('y', real=True)
    z = symbols('z', real=True)
    pi = pi
    E = E
    reals = S.Reals


"""

This function evaluates limits or returns a detailed error message with a reference code.
It allows the user to choose a language for responses, whenever applicable, via the locale parameter.

Author: Urate, Karen
Creation Date: 2025-12-01


Attributes
----------

expression: String
    This is the expression to evaluate.

symbol: Character
    This is the symbol choice to mark in the expression; the symbol must match the variable in the submitted expression.

approaches: String
    This is the target end of domain or range.

locale: String
    This is the preferred 3-letter language code, which can be any of the following: { ENG, FRA, SPA, KPR, JPN }

direction: Character
    If +, the expression will be evaluated for the domain that begins from the right.
    If -, the expression will be evaluated for the domain that begins from the left.
    If +-, the expression will be evaluated for the domain that compares left and right.

Returns
----------

result: Integer or Fraction
    Returns a Fraction object, if the result is not Integer, otherwise, Integer. 

"""
def lim(expression, symbol, approaches, locale='eng', direction=None):
    if direction is not None:
        direction = direction.strip()
    else:
        direction = ''

    if symbol not in expression:
        raise InvalidInputError(locale, "IIE001")
    elif (len(direction) > 0) and (direction != '+' and direction != '-' and direction != '+-'):
        raise InvalidInputError(locale, "IIE002")
    else:

        try:
            expr = parse_expr(expression, local_dict={symbol: symbols(symbol), "oo": oo})

            if approaches.strip().lower() == 'oo':
                approaches = oo
            elif approaches.strip().lower() == '-oo':
                approaches = -oo
            else:
                approaches = float(approaches)

            if len(direction) > 0:
                result = limit(expr, symbols(symbol), approaches, direction)
            else:
                result = limit(expr, symbols(symbol), approaches)

            return result

        except:
            raise InvalidInputError(locale, "IIE003")


"""

This is a special function to obtain the preferred simplified fraction version based on the specified maximum denominator. 
It raises an error if the input is invalid. 

Author: Urate, Karen
Creation Date: 2025-12-01


Attributes
----------

number: String
    This is the text version of the number to evaluate. It can be in a decimal, integer, or fraction (a/b) format.

locale: String (OPTIONAL)
    This is the preferred 3-letter language code, which can be any of the following: { ENG, FRA, SPA, KPR, JPN }

max_denominator: Integer (OPTIONAL)
    This is the preferred maximum denominator to generate a simplified fraction for. 


Returns
----------

fraction: Fraction
    This is the simplified converted fraction.

"""
def frac(number, locale='eng', max_denominator=200):
    if len(locale) != 3:
        locale = 'eng'

    try:
        number = float(number)
        result = Fraction(number).limit_denominator(max_denominator)
        return result
    except:
        raise InvalidInputError(locale, "IIE004")


"""

This is an approximation function to obtain the best maximum denominator for the fraction version of a float.
This function continuously approximates until the error rate for the best maximum denominator found is less then or equal to the specified error rate preferred.
By default, it searches by intervals of 100. The preferred interval can be modified through the interval parameter.

Author: Urate, Karen
Creation Date: 2025-12-01


Attributes
----------

number: Float
    This is the float number to obtain the fraction from.

interval: Integer (OPTIONAL)
    This is the preferred interval.

locale: String (OPTIONAL)
    This is the preferred 3-letter language code, which can be any of the following: { ENG, FRA, SPA, KPR, JPN }

err: Float
    This is the preferred error rate. Default is 4e-7.

Returns
----------

ideal: Integer
    This is the ideal maximum denominator based on interval and number.

"""
def get_ideal_denominator(number, interval=100, locale='eng', err=0.0000004):

    ideal = 1
    result = 0
    initial = interval

    try:
        number = float(number)
        result = Fraction(number).limit_denominator(initial)
        divergence = abs(float(number - ((result.numerator / result.denominator) * 1.0)))

        while ((result.numerator == 0) or (divergence > err)):
            initial = initial + interval
            result = Fraction(number).limit_denominator(initial)
            divergence = abs(float(number - ((result.numerator / result.denominator) * 1.0)))
        ideal = initial
        return ideal
    except Exception as e:
        print(e)
        raise InvalidInputError(locale.strip().lower(), "IIE003")


"""

This is a function to check if a fraction evaluates to an indeterminate form. 

Author: Urate, Karen
Creation Date: 2025-12-23


Attributes
----------

numerator: String
    This is the numerator of the fraction to evaluate.

denominator: String
    This is the denominator of the fraction to evaluate.

approaches: String
    This is the target end of domain or range.

Returns
----------

ind: Boolean
    Returns False, if the fraction is not in indeterminate form, otherwise, True.

"""
def is_indeterminate(numerator, denominator, approaches):

    num = lim(numerator, 'x', approaches, 'eng') if 'x' in numerator else numerator
    den = lim(denominator, 'x', approaches, 'eng') if 'x' in denominator else denominator
    ind = False

    if num == 0 and den == 0:
        ind = True
        return ind
    elif (num == Notations.inf or num == Notations.ninf) and (den == Notations.inf or num == Notations.ninf):
        ind = True
        return ind
    else:
        ind = False
        return ind

    return ind


"""

This is a special function to obtain the total number of PI in a float value
It raises an error if the input is invalid. 

Author: Urate, Karen
Creation Date: 2025-12-01


Attributes
----------

number: Float
    This is the number to evaluate.

locale: String (OPTIONAL)
    This is the preferred 3-letter language code, which can be any of the following: { ENG, FRA, SPA, KPR, JPN }


Returns
----------

pis: Integer or Fraction
    Returns an integer if the result is a whole number, otherwise, a fraction.

"""
def get_pi(number, locale='eng'):
    pis = 0
    if len(locale) != 3:
        locale = 'eng'

    try:
        number = float(number)
        pis = number / 3.141592653589793

        if pis.is_integer():
            return pis
        else:
            return Fraction(pis)
    except:
        raise InvalidInputError(locale, "IIE004")


"""

This is a special function to graph a limit equation.
It finds the best set of domain, if the limit exists, otherwise, uses the specified domain.
Array is not used for the arguments for immediate named access.

Author: Urate, Karen
Creation Date: 2025-12-08


Attributes
----------

expression: String
    This is the text version of the equation to plot in the graph.

center: Integer
    This is the x-value for the center point from the x-axis (red line). 

approaches: Integer
    This is the target x-value of the sought limit expression.

domain: Tuple
    This is the chosen domain, if specified.

figs: Tuple
    This is the dimensions of the displayed figure. Units are in inches.

xspace: Integer
    This is the linear space between x-values. 

"""
def graph(expression, center=0, approaches=1, domain=(-5, 5), figs=(10, 4), xspace=250):
    limit = lim(expression, 'x', str(approaches))
    expr = parse_expr(expression, local_dict={"x": Notations.x, "oo": oo})
    f_np = lambdify(Notations.x, expr, 'numpy')  # translates SymPy expressions into Python functions
    x_start = domain[0] if domain[0] < domain[1] else domain[1]
    x_end = domain[1] if domain[1] > domain[0] else domain[0]
    dlist = list(range(int(x_start - 1), int(x_end + 1)))
    conts = continuous_domain(expr, Notations.x, Notations.reals)

    cy = f_np(center) if center != 0 else f_np(abs(x_end - x_start) / 2)
    xc_label = f'center (x = {center}, y = {cy})' if center in conts else f'discontinuous at x={center}'

    fig, ax2 = plt.subplots(1, 1, figsize=figs)
    x_vals = np.linspace(x_start, x_end, xspace)
    y_vals = f_np(x_vals)  # range (Y)
    y_data = np.array(y_vals, dtype=float)
    mask = ~np.isnan(y_data)
    cleaned_y_data = y_data[mask]

    ax2.plot(x_vals, y_vals, label=f'f(x)')
    ax2.axvline(center, color='red', linestyle='--', label=xc_label)
    ax2.axhline(limit, color='green', linestyle=':', label=f'y as x -> {approaches} ({limit})')
    ax2.set_xlabel('x')
    ax2.set_ylabel('f(x)')
    ax2.legend()
    ax2.grid(True)
    ax2.set_xlim(x_start, x_end)
    ax2.set_ylim(min(cleaned_y_data) - 1.2, max(cleaned_y_data) + 1.2)
    lastcnt = x_start

    for pt in dlist:
        lastcnt = pt if pt in conts else lastcnt
        if pt not in conts:
            ax2.scatter(pt, f_np(lastcnt), color='red', marker='o', facecolor='white', s=50, zorder=5)
        else:
            ax2.scatter(pt, f_np(pt), color='black', marker='o', facecolor='blue', s=50, zorder=5)

    title = f'x = [{x_start:.2f},{x_end:.2f}]'
    title = title + f', y = [{(min(cleaned_y_data) - 1.2):.2f},{(max(cleaned_y_data) + 1.2):.2f}]'
    ax2.set_title(title)
    plt.tight_layout()
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=300)
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    graphic = base64.b64encode(image_png)
    graphic = graphic.decode('utf-8')

    return graphic


"""

This is a function to get the derivative of an expression.
This function returns a Tuple of the following values: (derivative, latex, and simplified).

Author: Urate, Karen
Creation Date: 2025-12-08


Attributes
----------

expression: String
    This is the text version of the equation to plot in the graph.

order: Integer
    The degree of derivative to obtain. Default is 1.

partial: Boolean
    When set to True, the function evaluations the expression for multiple variables.

Returns
----------

dv: Tuple (r, l, s, p)
    r: Expression - the derivative result
    t: Latex - the latex version of the derivative
    s: Expression - the simplified version of the derivative (for fractions and polynomials)
    p: Latex - the latex version of the simplified derivative (for fractions and polynomials)

"""
def differentiate(expression, order=1, partial=False):
    expr = parse_expr(expression, local_dict={"x": Notations.x, "y": Notations.y})
    result = None
    smpfied = None

    if 'y' in expression:
        result = idiff(expr, Notations.y, Notations.x)
    else:
        if order == 1:
            result = diff(expr, Notations.x)
        else:
            result = diff(expr, Notations.x, order)

    # common operations on result
    args = expand(simplify(result)).args
    smpfied = 0
    for a in args:
        smpfied = smpfied + sympy.radsimp(a)

    r = result
    t = latexify(result)
    s = smpfied
    p = latexify(smpfied)
    return (r, t, s, p)


"""

This is a function to obtain the Latex (v.2.7) of an expression.

Author: Urate, Karen
Creation Date: 2025-12-08

Attributes
----------

expression: String
    This is the expression to obtain a Latex version for.

"""
def latexify(expression):
    def get_mathjax_root(text="", version=2.7):
        match (version):
            case 2.7:
                text = text.replace("\sqrt[", "\\root[")
                return text

    expr = latex(expression)
    cleaned = get_mathjax_root(expr, 2.7)

    return cleaned


"""

This is a function to simplify a rational expression.
It returns a Tuple of the result and its latex version.

Author: Urate, Karen
Creation Date: 2025-12-08

Attributes
----------

expression: String
    This is the rational expression to simplify

"""
def simp_r(expression):
    def get_mathjax_root(text="", version=2.7):
        match (version):
            case 2.7:
                text.replace("\sqrt[", "\\root[")

    expr = parse_expr(expression, local_dict={"x": Notations.x})
    result = sympy.ratsimp(expr)

    return (result, get_mathjax_root(result, 2.7))


"""

This is a simple function to get the standard 26-letter Latin Alphabet array in lowercase or uppercase. 
It finds the best set of domain, if the limit exists, otherwise, uses the specified domain.

Author: Urate, Karen
Creation Date: 2025-12-15


Attributes
----------

lowercase: Boolean
    When set to False, the function returns an array of the 26-letter Latin Alphabet in uppercase, otherwise, lowercase.

"""
def get_abc(lowercase=True):
    if lowercase:
        return ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
                'v', 'w', 'x', 'y', 'z']
    else:
        return ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U',
                'V', 'W', 'X', 'Y', 'Z']


"""

This function returns a dictionary of unique elements and their respective quantity in a given substance.

Example:
    get_elements("RbNO3") returns {'Rb': 1, 'N': 1, 'O': 3}

Author: Urate, Karen
Creation Date: 2026-01-01

Attributes
----------

substance: String
    This is the substance to parse to generate the dictionary of elements with their respective original quantity.

"""
def get_elements(substance=""):
    uniques = dict()
    e = ""
    i = 0
    s = substance

    for ch in s:

        if len(ch) <= 0:
            continue
        if not ch.isnumeric() and (i == 0):
            e = e + ch
        elif not ch.isnumeric() and ch.islower() and i > 0:
            e = e + ch
        elif not ch.isnumeric() and ch.isupper():
            if e not in list(uniques.keys()):
                uniques[e] = 1
                e = ch
            else:
                uniques[e] = uniques[e] + 1
                e = ch
        elif not ch.isnumeric() and ((s[i - 1]).islower() and ch.isupper()) and i > 0:
            if e not in list(uniques.keys()):
                uniques[e] = 1
                e = ch
            else:
                uniques[e] = uniques[e] + 1
                e = ch
        elif ch.isnumeric() and not ((s[i - 1]).isnumeric()) and i > 0:
            t = ch
            j = i + 1

            if j < (len(s) - 2):
                while s[j].isnumeric() and j < len(s) - 1:
                    t = t + s[j] + ""
                    j = j + 1

            if e not in list(uniques.keys()):
                uniques[e] = int(t) if t.isnumeric() else 1
                e = ""
            else:
                uniques[e] = uniques[e] + 1
                e = ""

        elif ch.isnumeric() and ((s[i - 1]).isnumeric()) and i > 0:
            continue
        else:
            if e not in list(uniques.keys()):
                uniques[e] = 1
                e = ""
            else:
                uniques[e] = uniques[e] + 1
                e = ""
        i = i + 1

    # include only items with non-empty keys
    elements = dict()
    for key, value in uniques.items():
        if len(key) > 0:
            elements[key] = value

    return elements


"""

This function returns the dictionary of unique elements for a set of substances.


Author: Urate, Karen
Creation Date: 2026-01-01


Attributes
----------

keys: List
    This is the list of chemical substances to generate the dictionary for.

Returns
----------

element_dictionary: Dictionary
    This is the dictionary of unique elements for every chemical substance specified in the list.

"""
def get_substance_dictionary(keys=[]):
    element_dictionary = dict()

    for e in keys:
        element_dictionary[e] = get_elements(e)

    return element_dictionary


"""

This function returns the bootstrap code (v.5.3) for every chemical substance provided in a dictionary.

Author: Urate, Karen
Creation Date: 2026-01-01

Example
----------
OrderedDict( [('Rb1', 10), ('Rb1N1O3', 2)] ) returns:
    <span class=\"text-primary\">10</span>Rb <i class=\"fa-solid fa-plus\"></i> <span class=\"text-primary\">2</span>RbNO<sub>3</sub>

Example
----------
{'Rb2O1': 3} returns:
    <span class="text-primary">3</span>Rb<sub>2</sub>O


Attributes
----------

substances: Dictionary
    This is the dictionary of substances to generate the bootstrap code for.

type: String
    This is the type of equation to parse and generate the bootstrap code for. The only currently available value is chemistry. 

Returns
----------

bootstrapped: String
    This is the bootstrap code for the obtained balanced equation with Fontawesome icons.

"""
def get_bootstrap_code(substances=dict(), type="chemistry"):

    i = 0
    bootstrapped = ""
    for r in list(substances.keys()):

        if i > 0:
            bootstrapped = bootstrapped + (" <i class=\"fa-solid fa-plus\"></i> ")

        bootstrapped = bootstrapped + "<span class=\"text-primary\">" + str(substances[r]) + "</span>"
        for key, value in get_elements(r).items():
            bootstrapped = bootstrapped + key
            if value > 1:
                bootstrapped = bootstrapped + ("<sub>" + str(value) + "</sub>")
        i = i + 1
    return bootstrapped


"""

This function provides you with 3 sets of dictionaries: dictionary of unique elements for each reactant along with their original values, 
dictionary of unique elements for each product along with their original values, and a tuple of ordered dictionaries ({reactant},{product}) for the balanced equation.

This function also provides you with the bootstrap code for the obtained balanced equation.

Author: Urate, Karen
Creation Date: 2026-01-01


Attributes
----------

reactants: Set
    This is the set of reactants.

products: Set
    This is the set of products.

locale: String
    This is the preferred language.

Returns
----------

equation: Tuple (origs_r, origs_p, balanced, bootstrapped)
    origs_r: Dictionary - This is the dictionary of unique elements for each reactant along with their original values.
    origs_p: Dictionary - This is the dictionary of unique elements for each product along with their original values.
    balanced: Tuple - This is a tuple of ordered dictionaries ({reactant},{product}) for the balanced equation.
    bootstrapped: String - This is the bootstrap code for the obtained balanced equation with Fontawesome icons.

"""
def stoich(reactants={}, products={}, locale='eng'):
    try:
        balanced = balance_stoichiometry(reactants, products)
        origs_r = get_substance_dictionary(list(balanced[0].keys()))
        origs_p = get_substance_dictionary(list(balanced[1].keys()))
        reactant = get_bootstrap_code(balanced[0])
        product = " <i class=\"fa-solid fa-right-long\"></i> "
        product = product + get_bootstrap_code(balanced[1])
        bootstrapped = reactant + product
        return (origs_r, origs_p, balanced, bootstrapped)

    except Exception as error:
        raise InvalidInputError(locale.strip().lower(), "IIE005")


"""

This is the customized exception for Softhauz Calculus error-handling.

Author: Urate, Karen
Creation Date: 2025-12-01


Attributes
----------

locale: String
    This is the preferred 3-letter language code, which can be any of the following: { ENG, FRA, SPA, KPR, JPN }

error_code: String
    This is the error code reference used to obtain the message.

"""
class InvalidInputError(Exception):

    def __init__(self, locale, error_code):

        def get_message(locale, error_code):

            match (locale.strip().lower()):

                case 'eng':
                    if error_code == "IIE001":
                        return "The symbol entered does not exist in the submitted expression."
                    elif error_code == "IIE002":
                        return "The direction entered is invalid: it must be +, -, +-, or empty."
                    elif error_code == "IIE003":
                        return "The submitted expression cannot be evaluated."
                    elif error_code == "IIE004":
                        return "The input is not numeric and invalid."
                    elif error_code == "IIE005":
                        return "You have entered an invalid chemical reaction. Please check your equation and try again."

                case 'fra':
                    if error_code == "IIE001":
                        return "Le symbole saisi n'existe pas dans l'expression soumise."
                    elif error_code == "IIE002":
                        return "La direction saisie est invalide : elle doit être +, -, +-, ou vide."
                    elif error_code == "IIE003":
                        return "L'expression soumise ne peut pas être évaluée."
                    elif error_code == "IIE004":
                        return "L'entrée n'est pas numérique et est invalide."
                    elif error_code == "IIE005":
                        return "Vous avez saisi une réaction chimique invalide. Veuillez vérifier votre équation et réessayer."

                case 'spa':
                    if error_code == "IIE001":
                        return "El símbolo introducido no existe en la expresión enviada."
                    elif error_code == "IIE002":
                        return "La dirección introducida no es válida: debe ser +, -, +-, o estar vacía."
                    elif error_code == "IIE003":
                        return "La expresión enviada no se puede evaluar."
                    elif error_code == "IIE004":
                        return "La entrada no es numérica y no es válida."
                    elif error_code == "IIE005":
                        return "Ha introducido una reacción química no válida. Por favor, revise la ecuación e inténtelo de nuevo."

                case 'kor':
                    if error_code == "IIE001":
                        return "입력된 기호는 제출된 수식에 존재하지 않습니다."
                    elif error_code == "IIE002":
                        return "입력된 방향이 잘못되었습니다. +, -, +-, 또는 빈칸만 입력할 수 있습니다."
                    elif error_code == "IIE003":
                        return "제출된 표현식은 평가할 수 없습니다."
                    elif error_code == "IIE004":
                        return "입력값이 숫자가 아니므로 유효하지 않습니다."
                    elif error_code == "IIE005":
                        return "잘못된 화학 반응식을 입력하셨습니다. 방정식을 확인하고 다시 시도해 주세요."

                case 'jpn':
                    if error_code == "IIE001":
                        return "入力された記号は送信された式に存在しません。"
                    elif error_code == "IIE002":
                        return "入力された方向が無効です。+、-、+-、または空白にする必要があります。"
                    elif error_code == "IIE003":
                        return "送信された式は評価できません。"
                    elif error_code == "IIE004":
                        return "入力は数値ではなく無効です。"
                    elif error_code == "IIE005":
                        return "無効な化学反応式が入力されました。式を確認してもう一度お試しください。"

        self.message = get_message(locale, error_code)
        super().__init__(self.message)
        self.error_code = error_code

    def __str__(self):
        return f"{self.message} (SOFTHAUZ ERROR CODE: {self.error_code})"


"""

This is a function to generate a random timestamped token that can be used for automation of passwords or unique identifiers.
The optional prefix is added at the front of the token, if classification is preferred.

Author: Urate, Karen
Creation Date: 2025-01-08


Attributes
----------

prefix: String (OPTIONAL)
    This is the preferred prefix to put at the front of the token.

Returns
----------

token: String 
    This is the generated token.    

"""
def generate_random_token(prefix="STUDENT"):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d|%H:M')
    token = str(prefix).strip() + str(uuid.uuid4()) + timestamp
    return token


"""

This is a function to generate a random set of unique users with username, first name, surname, date of birth, registration date,
last login, province, country, and generated password.
The default country for the provinces in the generated user profiles is Canada.

Author: Urate, Karen
Creation Date: 2025-01-08


Attributes
----------

total: Integer (OPTIONAL)
    This is the total number of unique users to generate.

Returns
----------

users: Dictionary 
    This is the 2D dictionary of random users in a key-value pair: { <username>: { <attribute>:  ... }, ... }

"""
def generate_users(total=15):

    num_records = total
    faker = Faker('en_US')
    users = dict()
    profiles = [faker.simple_profile() for i in range(num_records)]
    usernames = [faker.unique.first_name() + str(random.randint(11, 35)) for i in range(num_records)]
    firstnames = [faker.unique.first_name() for i in range(num_records)]
    surnames = [faker.unique.last_name() for i in range(num_records)]
    emails = [faker.unique.email() for i in range(num_records)]
    provinces = ['Alberta', 'British Columbia', 'Manitoba', 'Saskatchewan', 'Ontario',
                 'Québec', 'Prince Edward Island', 'Nova Scotia', 'Northwest Territories',
                 'Yukon', 'New Brunswick', 'Newfoundland and Labrador', 'Nunavut']
    password = generate_random_token()

    for i in range(num_records):
        rint = random.randint(0, num_records - 1)
        year = int(profiles[rint]['birthdate'].strftime("%Y"))
        month = int(profiles[rint]['birthdate'].strftime("%m"))
        day = int(profiles[rint]['birthdate'].strftime("%d"))
        random_login = datetime.date(random.randint(2000, 2026), month, day)
        token = "USER-" + generate_random_token()
        province = str(provinces[random.randint(0, 12)])

        users[usernames[i]] = {
            "password": password,
            "registration_date": str(datetime.datetime.now()),
            "last_login": random_login,
            "email": str(emails[i]),
            "dob": datetime.date(year, month, day),
            "first_name": str(firstnames[i]),
            "last_name": str(surnames[i]),
            "province": province,
            "country": str('CA'),
            "token": token
        }

    return users