from math import lcm
from flask import Flask, render_template, request


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

@app.route("/", methods=["GET", "POST"])
def index():
    valid_input = True
    try:
        N = int(request.form.get("N"))
    except:
        N = 9
    right_to_left = False
    hide_fp = False

    # Store user inputs in variables
    if not request.form.get("input"):
        s = ""
    else:
        s = request.form.get("input").strip()
    if request.form.get("Right to left?"):
        right_to_left = True
    if request.form.get("Hide fixed points?"):
        hide_fp = True
    if N not in range(1,10):
        valid_input = False
        N = 9

    # Convert user input to permutation
    try:
        perm = string_to_perm(s, right_to_left, N, hide_fp)
    except:
        valid_input = False
        perm = string_to_perm("", right_to_left, N, hide_fp)
    
    return render_template("index.html", s=s, perm=perm, N=N, right_to_left=right_to_left,
                           hide_fp=hide_fp, valid_input=valid_input)


class Cycle:
    def __init__(self, numbers, N):
        self.numbers = numbers
        self.N = N

    def __str__(self):
        s = "("
        for i in self.numbers:
            s += str(i) + " "
        return s.rstrip() + ")"

    # Return length of cycle
    def length(self):
        return len(self.numbers)

    # Return map associated with cycle
    def to_map(self):
        f = identity(self.N)
        for i in range(self.length()):
            f[self.numbers[i]] = self.numbers[(i + 1) % self.length()]
        return f


class Permutation:
    def __init__(self, cycles, N, hide_fp):
        self.cycles = cycles
        self.N = N
        self.hide_fp = hide_fp

    def __str__(self):
        s = ""
        for cycle in self.cycles:
            if cycle.length() != 1 or not self.hide_fp:
                s += str(cycle)
        return s

    # Return map associated with permutation
    def to_map(self):
        f = identity(self.N)
        for cycle in self.cycles:
            f = multiply_maps([f, cycle.to_map()], True, self.N)
        return f

    # Return list of lengths of constituent cycles
    def lengths(self):
        return [cycle.length() for cycle in self.cycles]

    # Return order of permutation
    def order(self):
        return lcm(*self.lengths())

    # Return sign of permutation
    def sign(self):
        if (sum(self.lengths()) - self.number_cycles()) % 2 == 0:
            return 1
        else:
            return -1

    # Return number of cycles
    def number_cycles(self):
        return len(self.cycles)

    # Return number of inversions
    def inversions(self):
        inversions = 0
        f = self.to_map()

        for i in digits(self.N):
            for j in range(i + 1, self.N + 1):
                if f[i] > f[j]:
                    inversions += 1
        return inversions

    # Return nth power of permutation
    def nth_power(self, n):
        f = self.to_map()
        k = n % self.order()
        maps = [f for i in range(k)]
        return cycle_decomp(multiply_maps(maps, True, self.N), self.N, self.hide_fp)

    # Return inverse of permutation
    def inverse(self):
        return self.nth_power(-1)

    # Return fixed points of permutation
    def fp(self):
        fp = []
        for i in range(self.number_cycles()):
            if self.lengths()[i] == 1:
                fp.append(self.cycles[i].numbers[0])
        return fp

    # Return permuted points of permutation
    def not_fp(self):
        points = []
        for i in digits(self.N):
            if i not in self.fp():
                points.append(i)
        return points


# Convert map to Permutation object via cycle decomp
def cycle_decomp(f, N, hide_fp):
    cycles = []
    used = []

    # Cycle decomposition algorithm
    for i in digits(N):
        if i not in used:
            cycle = find_cycle(f, [i], i, N)
            cycles.append(cycle)
            used.extend(cycle.numbers)
        
    return Permutation(cycles, N, hide_fp)


# Use recursion to find the cycle of a map containing i
def find_cycle(f, numbers, i, N):
    if f[i] == numbers[0]:
        return Cycle(numbers, N)
    else:
        numbers.append(f[i])
        return find_cycle(f, numbers, f[i], N)


# Multiply maps
def multiply_maps(maps, right_to_left, N):
    prod = identity(N)
    for i in range(len(maps)):
        for j in digits(N):
            if right_to_left:
                prod[j] = maps[len(maps) - 1 - i][prod[j]]
            else:
                prod[j] = maps[i][prod[j]]
    return prod


# Convert user input string to a list of maps
def string_to_maps(s, N, hide_fp):
    maps = []

    i = 0
    while i < len(s):
        # Look for cycle
        if s[i] == "(":
            j = s.find(")", i)
            f = cycle_string_to_map(s[i + 1:j], N)
            maps.append(f)
            i = j + 1

            if not f or j == -1:
                return None

        # Look for one-line
        elif s[i] == "[":
            j = s.find("]", i)
            f = one_line_string_to_map(s[i + 1:j], N)
            maps.append(f)
            i = j + 1

            if not f or j == -1:
                return None

        # Look for exponent
        elif s[i] == "^":
            exponent = ""
            i += 1
            print(maps)

            if i < len(s) and s[i] == "-":
                exponent = "-"
                i += 1
            while i < len(s) and s[i].isnumeric():
                exponent += s[i]
                i += 1
            if not exponent or exponent == "-" or not maps:
                return None 

            maps[-1] = cycle_decomp(maps[-1], N, hide_fp).nth_power(int(exponent)).to_map()

        else:
            return None

    return maps


# Converts a string to a map
# Returns error if not in cycle notation, minus ( and )
def cycle_string_to_map(s, N):
    s = s.split()

    # Check that the string contains at most N values,
    # and these values are all distinct, valid digits
    if len(s) > N or duplicates(s) or not set(s).issubset(set(map(str, digits(N)))):
        return None

    # Use s to construct and return a cycle
    return Cycle(list(map(int, s)), N).to_map()


# Converts a string to a map
# Returns error if not in one-line notation, minus [ and ]
def one_line_string_to_map(s, N):
    s = s.split()

    # Check that the string contains N values,
    # and these values are all distinct, valid digits
    if len(s) != N or set(s) != set(map(str, digits(N))):
        return None

    # Use s to construct and return a map
    f = {}
    for i in digits(N):
        f[i] = int(s[i-1])
    return f


# Converts a user's string to a permutation
def string_to_perm(s, right_to_left, N, hide_fp):
    return cycle_decomp(multiply_maps(string_to_maps(s, N, hide_fp), right_to_left, N), N, hide_fp)


# Return list of digits
def digits(N):
    return list(range(1, N + 1))


# Return identity function based on N
def identity(N):
    identity = {}
    for i in digits(N):
        identity[i] = i
    return identity


# Check for duplicates in a list
def duplicates(lst):
    a = set()
    for x in lst:
        if x in a:
            return True
        else:
            a.add(x)
    return False