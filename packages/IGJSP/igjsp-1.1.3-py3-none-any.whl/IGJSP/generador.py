import copy
import datetime
import json
import os
import pickle
import re
from itertools import combinations

import networkx as nx
import numpy as np

np.set_printoptions(linewidth=np.inf, threshold=np.inf, formatter={"int": lambda x: f"{x}"})

from pprint import pprint

from scipy.stats import expon, norm, uniform

from importlib.resources import files, as_file

def _read_text_resource(rel_path: str, encoding: str = "utf-8") -> str:
    p = files("IGJSP").joinpath(rel_path)
    if not p.is_file():
        raise FileNotFoundError(
            f"Template Minizinc no encontrado en el paquete: {rel_path}"
        )
    return p.read_text(encoding=encoding)

def f(x):
    return int(np.exp(-int(x)/100)*100)

def g(x):
    return 90*x + 10

def t(c):
    return 4.0704 * np.log(2) / np.log(1 + (c* 2.5093)**3)


# ------- Helpers internos para el DZN -------


def _parse_set_size(text, name):
    """
    Obtiene el tamaño de un conjunto tipo:
        JOBS = 1..50;
    Devuelve 50.
    """
    m = re.search(rf'\b{name}\b\s*=\s*1\.\.(\d+)\s*;', text)
    if not m:
        raise ValueError(f"No se pudo encontrar el conjunto {name} = 1..N; en el fichero DZN.")
    return int(m.group(1))


def _parse_speed(text):
    """
    SPEED puede ir como:
        SPEED = 1;
    o (por si acaso) como 1..SPEED; (aunque en tu ejemplo es un escalar).
    """
    m = re.search(r'\bSPEED\b\s*=\s*(\d+)\s*;', text)
    if m:
        return int(m.group(1))

    m = re.search(r'\bSPEED\b\s*=\s*1\.\.(\d+)\s*;', text)
    if m:
        return int(m.group(1))

    # Si no aparece, asumimos 1 (como en muchos templates tuyos)
    return 1


def _parse_array_from_arrayXd(text, name):
    """
    Extrae la parte entre corchetes de cosas tipo:
        name = array3d(...,[1,2,3,...]);
        name = array2d(...,[1,2,3,...]);
        name = array1d(...,[1,2,3,...]);

    Devuelve np.array de ints o None si no se encuentra.
    """
    m = re.search(
        rf'\b{name}\b\s*=\s*array[123]d\([^[]*\[\s*(.*?)\s*\]\s*\)\s*;',
        text,
        re.DOTALL
    )
    if not m:
        return None

    inner = m.group(1).strip()
    if not inner:
        return np.array([], dtype=int)

    # Separar por comas o espacios
    tokens = re.split(r'[\s,]+', inner)
    tokens = [t for t in tokens if t != '']

    return np.array([int(t) for t in tokens], dtype=int)


def _parse_array_fallback_plain(text, name):
    """
    Fallback para cosas tipo:
        name = [1,2,3,...];
    por si en algún template no se usa arrayXd.
    """
    m = re.search(
        rf'\b{name}\b\s*=\s*\[\s*(.*?)\s*\]\s*;',
        text,
        re.DOTALL
    )
    if not m:
        return None

    inner = m.group(1).strip()
    if not inner:
        return np.array([], dtype=int)

    tokens = re.split(r'[\s,]+', inner)
    tokens = [t for t in tokens if t != '']

    return np.array([int(t) for t in tokens], dtype=int)


def _parse_array_generic(text, name):
    """
    Intenta primero arrayXd(...,[...]); y si no lo encuentra,
    prueba el formato plano name = [ ... ];
    """
    arr = _parse_array_from_arrayXd(text, name)
    if arr is not None:
        return arr
    return _parse_array_fallback_plain(text, name)

#################################################################################
#                                                                               # 
#                                    JSP                                       # 
#                                                                               #
#################################################################################

class JSP:
    def __init__(self, jobs, machines, ProcessingTime=np.array([]), EnergyConsumption=np.array([]), ReleaseDateDueDate=np.array([]), Orden=np.array([])) -> None:       
        self.numJobs = jobs
        self.numMchs = machines
        self.speed = ProcessingTime.shape[-1] if ProcessingTime.size else 0
        self.ProcessingTime = ProcessingTime
        self.EnergyConsumption = EnergyConsumption
        self.Orden = Orden
        self.rddd = ReleaseDateDueDate.ndim - 1 if ReleaseDateDueDate.size else 0
        
    def fill_random_values(self, speed, rddd, distribution, seed, tpm=[]):
        np.random.seed(seed)
        self.rddd = rddd
        self.speed = speed
        if not tpm or len(tpm) != self.numMchs:
            if distribution == "uniform":
                tpm = np.random.uniform(10, 100, self.numMchs)
            elif distribution == "normal":
                tpm = [max(10, data) for data in np.random.normal(50, 20, self.numMchs)]
            else:
                tpm = expon(loc=10, scale=20).rvs(self.numMchs)
       
        energyPer, timePer = self._particionate_speed_space(speed)
        self._generate_standar_operation_cost(distribution)

        self.ProcessingTime = np.zeros((self.numJobs, self.numMchs, self.speed), dtype=int)
        self.EnergyConsumption = np.zeros((self.numJobs, self.numMchs, self.speed), dtype=int)
        self.Orden = np.zeros((self.numJobs, self.numMchs), dtype=int)

        if self.rddd == 0:
            release_date_tasks = np.array([0] * self.numJobs)
        
        elif self.rddd == 1:
            release_date_tasks = np.random.choice(range(0, 101, 10), self.numJobs)
            release_date_tasks = release_date_tasks - release_date_tasks.min()
            self.ReleaseDueDate = np.zeros((self.numJobs, 2), dtype=int)

        elif self.rddd == 2:
            release_date_tasks = np.random.choice(range(0, 101, 10), self.numJobs)
            release_date_tasks = release_date_tasks - release_date_tasks.min()
            self.ReleaseDueDate = np.zeros((self.numJobs, self.numMchs, 2), dtype=int)

        self._jobToMachine(release_date_tasks, timePer, distribution)
        self.generate_maxmin_objective_values()

    def _particionate_speed_space(self, speed):
        energyPer = np.linspace(0.5, 3, speed) if speed > 1 else [1]
        timePer = [t(c) for c in energyPer]
        return energyPer, timePer

    def _generate_standar_operation_cost(self, distribution):
        if distribution == "uniform":
            self.operationCost = np.random.uniform(10, 100, (self.numJobs, self.numMchs))
        elif distribution == "normal":
            self.operationCost = np.array([max(10, x) for x in np.random.normal(50, 20, (self.numJobs, self.numMchs)).reshape(-1)]).reshape(self.numJobs, self.numMchs)
        elif distribution == "exponential":
            self.operationCost = np.random.exponential(10, (self.numJobs, self.numMchs))

    def _jobToMachine(self, release_date_tasks, timePer, distribution):
        for job in range(self.numJobs):
            machines = np.random.choice(range(self.numMchs), self.numMchs, replace=False)
            self.Orden[job] = machines
            releaseDateTask = release_date_tasks[job]
            initial = releaseDateTask
            for machine in machines:
                for S, (proc, energy) in enumerate(self._genProcEnergy(job, machine, timePer)):
                    self.ProcessingTime[job, machine, S] = proc
                    self.EnergyConsumption[job, machine, S] = energy
                if self.rddd == 2:
                    self.ReleaseDueDate[job, machine, 0] = releaseDateTask
                    releaseDateTask += int(self._release_due(np.median(self.ProcessingTime[job, machine, :]), distribution))
                    self.ReleaseDueDate[job, machine, 1] = releaseDateTask
                else:
                    releaseDateTask += np.median(self.ProcessingTime[job, machine, :])
            if self.rddd == 1:
                self.ReleaseDueDate[job] = [initial, int(self._release_due(releaseDateTask, distribution))]

    def _genProcEnergy(self, job, machine, timePer):        
        ans = []  
        for tper in timePer:
            time = max(1, self.operationCost[job, machine] * tper)
            ans.append((time, max(1, f(time))))
        return ans

    def _release_due(self, duration, distribution):
        if distribution == "uniform":
            return uniform(duration, 2*duration).rvs()
        elif distribution == "normal":
            return max(duration, norm(loc=2*duration, scale=duration/2).rvs())
        else:
            return expon(loc=duration, scale=duration/2).rvs()

    def loadPythonFile(path):
        """
        Carga un fichero .pkl generado por savePythonFile y devuelve un JSP.
        """
        with open(path, 'rb') as f:
            obj = pickle.load(f)

        # Si ya es un JSP, lo devolvemos tal cual
        if isinstance(obj, JSP):
            return obj

        # Si es un dict con la misma estructura que usamos en loadJsonFile, construimos el JSP
        if isinstance(obj, dict) and all(
            k in obj for k in ['jobs', 'machines', 'ProcessingTime', 'EnergyConsumption', 'ReleaseDateDueDate', 'Orden']
        ):
            return JSP(**obj)

        raise TypeError(
            f"El objeto cargado desde {path} no es un JSP ni un diccionario compatible para construir uno."
        )

    def loadDznFile(path):
        """
        Carga un .dzn generado a partir de tus templates, del estilo:

            JOBS = 1..J;
            MACHINES = 1..M;
            SPEED = S;

            time = array3d(JOBS,MACHINES,1..SPEED,[...]);
            energy = array3d(JOBS,MACHINES,1..SPEED,[...]);
            precedence = array2d(JOBS,MACHINES,[...]);

        Opcionalmente puede contener:
            releaseDate = array1d(JOBS,[...])  (rddd = 1)
            dueDate     = array1d(JOBS,[...])

        o

            releaseDate = array2d(JOBS,MACHINES,[...])  (rddd = 2)
            dueDate     = array2d(JOBS,MACHINES,[...])

        Devuelve un objeto JSP(**sol) consistente con loadJsonFile.
        """
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Eliminar comentarios de Minizinc (% hasta final de línea)
        text = re.sub(r'%.*', '', text)

        # Leer tamaños de conjuntos
        numJobs = _parse_set_size(text, "JOBS")
        numMchs = _parse_set_size(text, "MACHINES")
        speed = _parse_speed(text)

        # Leer arrays principales
        time_flat = _parse_array_generic(text, "time")
        energy_flat = _parse_array_generic(text, "energy")
        prec_flat = _parse_array_generic(text, "precedence")

        if time_flat is None or energy_flat is None or prec_flat is None:
            raise ValueError("No se pudieron leer 'time', 'energy' o 'precedence' del fichero DZN.")

        expected_te = numJobs * numMchs * speed
        if time_flat.size != expected_te or energy_flat.size != expected_te:
            raise ValueError(
                f"Tamaños incompatibles en time/energy: esperado {expected_te}, "
                f"time={time_flat.size}, energy={energy_flat.size}"
            )

        expected_prec = numJobs * numMchs
        if prec_flat.size != expected_prec:
            raise ValueError(
                f"Tamaño incompatible en precedence: esperado {expected_prec}, precedence={prec_flat.size}"
            )

        ProcessingTime = time_flat.reshape((numJobs, numMchs, speed))
        EnergyConsumption = energy_flat.reshape((numJobs, numMchs, speed))
        precedence = prec_flat.reshape((numJobs, numMchs))

        # Reconstruir Orden a partir de precedence (igual que en saveDznFile)
        # precedence[j, m] = posición de la máquina m en la secuencia 0..M-1
        Orden = np.zeros((numJobs, numMchs), dtype=int)
        for j in range(numJobs):
            Orden[j, :] = np.argsort(precedence[j, :])

        # --- Release / Due dates (si existen) ---
        release_flat = _parse_array_generic(text, "releaseDate")
        due_flat = _parse_array_generic(text, "dueDate")

        if release_flat is None or due_flat is None:
            # rddd = 0 (no fechas)
            ReleaseDueDate = np.array([])
        else:
            if release_flat.size == numJobs and due_flat.size == numJobs:
                # rddd = 1: job-level
                ReleaseDueDate = np.zeros((numJobs, 2), dtype=int)
                ReleaseDueDate[:, 0] = release_flat
                ReleaseDueDate[:, 1] = due_flat
            elif release_flat.size == numJobs * numMchs and due_flat.size == numJobs * numMchs:
                # rddd = 2: operation-level
                ReleaseDueDate = np.zeros((numJobs, numMchs, 2), dtype=int)
                ReleaseDueDate[:, :, 0] = release_flat.reshape((numJobs, numMchs))
                ReleaseDueDate[:, :, 1] = due_flat.reshape((numJobs, numMchs))
            else:
                raise ValueError(
                    "Los tamaños de releaseDate/dueDate no cuadran ni con rddd=1 ni con rddd=2."
                )

        sol = {
            'jobs': numJobs,
            'machines': numMchs,
            'ProcessingTime': ProcessingTime,
            'EnergyConsumption': EnergyConsumption,
            'ReleaseDateDueDate': ReleaseDueDate,
            'Orden': Orden
        }

        return JSP(**sol)

    def loadTaillardFile(path):
        """
        Carga un fichero de texto generado por saveTaillardStandardFile y devuelve un JSP.
        Formato esperado:

            Number of jobs: J
            Number of machines: M

            Processing times:
            ... J filas, cada una con M enteros ...

            Energy consumption:
            ... J filas, cada una con M enteros ...

            Machine order:
            ... J filas, cada una con M enteros ...
        """
        with open(path, 'r') as f:
            lines = [line.strip() for line in f]

        # Leer encabezado
        # Number of jobs: X
        # Number of machines: Y
        numJobs = None
        numMchs = None

        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("Number of jobs"):
                numJobs = int(line.split(":")[1].strip())
            elif line.startswith("Number of machines"):
                numMchs = int(line.split(":")[1].strip())
            if numJobs is not None and numMchs is not None:
                i += 1
                break
            i += 1

        if numJobs is None or numMchs is None:
            raise ValueError("No se pudieron leer numJobs / numMchs del fichero Taillard.")

        # Saltar líneas vacías hasta "Processing times:"
        while i < len(lines) and lines[i] == "":
            i += 1
        if i >= len(lines) or not lines[i].startswith("Processing times"):
            raise ValueError("No se encontró la sección 'Processing times:' en el fichero Taillard.")
        i += 1  # pasar la línea de cabecera

        # Leer matriz de tiempos de procesamiento (J filas)
        proc_by_order = np.zeros((numJobs, numMchs), dtype=int)
        for j in range(numJobs):
            while i < len(lines) and lines[i] == "":
                i += 1
            parts = lines[i].split()
            if len(parts) != numMchs:
                raise ValueError(
                    f"Línea de tiempos de procesamiento para job {j} tiene {len(parts)} elementos, "
                    f"pero se esperaban {numMchs}."
                )
            proc_by_order[j, :] = [int(x) for x in parts]
            i += 1

        # Saltar hasta "Energy consumption:"
        while i < len(lines) and lines[i] == "":
            i += 1
        if i >= len(lines) or not lines[i].startswith("Energy consumption"):
            raise ValueError("No se encontró la sección 'Energy consumption:' en el fichero Taillard.")
        i += 1  # cabecera

        energy_by_order = np.zeros((numJobs, numMchs), dtype=int)
        for j in range(numJobs):
            while i < len(lines) and lines[i] == "":
                i += 1
            parts = lines[i].split()
            if len(parts) != numMchs:
                raise ValueError(
                    f"Línea de consumo de energía para job {j} tiene {len(parts)} elementos, "
                    f"pero se esperaban {numMchs}."
                )
            energy_by_order[j, :] = [int(x) for x in parts]
            i += 1

        # Saltar hasta "Machine order:"
        while i < len(lines) and lines[i] == "":
            i += 1
        if i >= len(lines) or not lines[i].startswith("Machine order"):
            raise ValueError("No se encontró la sección 'Machine order:' en el fichero Taillard.")
        i += 1  # cabecera

        Orden = np.zeros((numJobs, numMchs), dtype=int)
        for j in range(numJobs):
            while i < len(lines) and lines[i] == "":
                i += 1
            parts = lines[i].split()
            if len(parts) != numMchs:
                raise ValueError(
                    f"Línea de orden de máquinas para job {j} tiene {len(parts)} elementos, "
                    f"pero se esperaban {numMchs}."
                )
            Orden[j, :] = [int(x) for x in parts]
            i += 1

        # Reconstruir ProcessingTime y EnergyConsumption con speed=1
        speed = 1
        ProcessingTime = np.zeros((numJobs, numMchs, speed), dtype=int)
        EnergyConsumption = np.zeros((numJobs, numMchs, speed), dtype=int)

        for j in range(numJobs):
            for pos in range(numMchs):
                machine = Orden[j, pos]
                ProcessingTime[j, machine, 0] = proc_by_order[j, pos]
                EnergyConsumption[j, machine, 0] = energy_by_order[j, pos]

        # Taillard estándar: sin release/due dates → rddd=0
        ReleaseDueDate = np.array([])

        sol = {
            'jobs': numJobs,
            'machines': numMchs,
            'ProcessingTime': ProcessingTime,
            'EnergyConsumption': EnergyConsumption,
            'ReleaseDateDueDate': ReleaseDueDate,
            'Orden': Orden
        }
        return JSP(**sol)
        
    def loadJsonFile(path):
        with open(path, "r") as f:
            data = json.load(f)
        numJobs = len(data["nbJobs"])
        numMchs = len(data["nbMchs"])
        speed = data["speed"]
    
        # # Load KPIs (opcional)
        # min_makespan = data.get("minMakespan", None)
        # min_energy = data.get("minEnergy", None)
        # max_min_makespan = data.get("maxMinMakespan", None)
        # max_min_energy = data.get("maxMinEnergy", None)
    
        # Prepare empty structures
        ProcessingTime = np.zeros((numJobs, numMchs, speed), dtype=int)
        EnergyConsumption = np.zeros((numJobs, numMchs, speed), dtype=int)
        Orden_list = [[] for _ in range(numJobs)]
    
        # Detect rddd mode
        # rddd = 0 → no release/due dates
        # rddd = 1 → job-level RDF
        # rddd = 2 → operation-level RDF
        rddd = 0
        if data["timeEnergy"]:
            if "release-date" in data["timeEnergy"][0]:
                rddd = 1
            for m in data["timeEnergy"][0]["operations"]:
                if "release-date" in data["timeEnergy"][0]["operations"][m]:
                    rddd = 2
                    break
    
        # Initialize ReleaseDueDate array according to rddd
        if rddd == 1:
            ReleaseDueDate = np.zeros((numJobs, 2), dtype=int)
        elif rddd == 2:
            ReleaseDueDate = np.zeros((numJobs, numMchs, 2), dtype=int)
        else:
            # No dates: devolver array vacío para que __init__ detecte rddd=0
            ReleaseDueDate = np.array([])
    
        # -------------------------
        # Load jobs & operations
        # -------------------------
        for job_data in data["timeEnergy"]:
            job = int(job_data["jobId"])
    
            # Optional job-level release/due dates
            if rddd == 1:
                ReleaseDueDate[job, 0] = int(job_data["release-date"])
                ReleaseDueDate[job, 1] = int(job_data["due-date"])
    
            for machine_str, op_data in job_data["operations"].items():
                machine = int(machine_str)
                Orden_list[job].append(machine)
    
                # Load speed-scaling arrays
                proc_times = [int(entry["procTime"]) for entry in op_data["speed-scaling"]]
                energies = [int(entry["energyCons"]) for entry in op_data["speed-scaling"]]
    
                # Aseguramos longitud speed
                # Si speed > len(proc_times) -> rellenamos con ceros (o ajustar según tu política)
                proc_arr = np.zeros((speed,), dtype=int)
                en_arr = np.zeros((speed,), dtype=int)
                L = min(len(proc_times), speed)
                proc_arr[:L] = proc_times[:L]
                en_arr[:L] = energies[:L]
    
                ProcessingTime[job, machine, :] = proc_arr
                EnergyConsumption[job, machine, :] = en_arr
    
                if rddd == 2:
                    ReleaseDueDate[job, machine, 0] = int(op_data["release-date"])
                    ReleaseDueDate[job, machine, 1] = int(op_data["due-date"])
    
        # Convertir Orden a ndarray (shape = numJobs x numMchs)
        Orden = np.zeros((numJobs, numMchs), dtype=int)
        for j in range(numJobs):
            if len(Orden_list[j]) != numMchs:
                # Si por algun motivo no tiene todas las máquinas,
                # rellenamos con -1 o lanzamos error; aquí uso -1.
                row = Orden_list[j] + [-1] * (numMchs - len(Orden_list[j]))
            else:
                row = Orden_list[j]
            Orden[j, :] = np.array(row, dtype=int)
    
        sol = {
            'jobs': numJobs,
            'machines': numMchs,
            'ProcessingTime': ProcessingTime,
            'EnergyConsumption': EnergyConsumption,
            'ReleaseDateDueDate': ReleaseDueDate,   # <-- ahora es array, no int
            'Orden': Orden
        }
        return JSP(**sol)

    def saveJsonFile(self, path):
        self.JSP = {
            "nbJobs": list(range(self.numJobs)),
            "nbMchs": list(range(self.numMchs)),
            "speed": self.speed,
            "timeEnergy": [],
            "minMakespan": int(self.min_makespan),
            "minEnergy": int(self.min_energy),
            "maxMinMakespan": int(self.max_min_makespan),
            "maxMinEnergy": int(self.max_min_energy)
        }
        
        for job in range(self.numJobs):
            new = {
                "jobId": job,
                "operations": {},
            }

            for machine in self.Orden[job]:
                machine = int(machine)
                new["operations"][machine] = {"speed-scaling" : 
                                            [
                                                {"procTime" : int(proc),
                                                "energyCons" : int(energy)
                                                }
                                                for proc, energy in zip(self.ProcessingTime[job, machine],self.EnergyConsumption[job, machine])
                                            ]
                                            }
                if self.rddd == 2:
                    new["operations"][machine]["release-date"] = int(self.ReleaseDueDate[job][machine][0])
                    new["operations"][machine]["due-date"] = int(self.ReleaseDueDate[job][machine][1])
            if self.rddd == 1:
                new["release-date"] = int(self.ReleaseDueDate[job][0])
                new["due-date"] = int(self.ReleaseDueDate[job][1])
            if self.rddd == 2:
                new["release-date"] = int(min(self.ReleaseDueDate[job, :, 0]))
                new["due-date"] = int(max(self.ReleaseDueDate[job, :, 1]))
            self.JSP["timeEnergy"].append(new)

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w+') as f:
            # Generamos el JSON con indentación normal
            json_str = json.dumps(self.JSP, indent=4)
            
            # Compresión selectiva: solo arrays de números simples
            def compress_simple_arrays(match):
                # Comprimir si el array contiene solo números y comas
                content = match.group(1)
                if re.match(r'^(\s*\d+\s*,)*\s*\d+\s*$', content):
                    # Eliminar espacios y saltos de línea
                    return '[' + re.sub(r'\s+', '', content) + ']'
                return match.group(0)  # Mantener como está si no es simple
            
            # Buscar arrays que puedan comprimirse
            json_str = re.sub(
                r'\[([\s\S]*?)\]', 
                compress_simple_arrays, 
                json_str,
                flags=re.DOTALL
            )
            
            f.write(json_str)

    def savePythonFile(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(self, f)

    def saveDznFile(self, InputDir, OutputDir,index):
        indexProblema = OutputDir.split("/")[-2]
        OutputDir = "/".join(OutputDir.split("/")[:-2])
        # indexProblema = os.path.basename(os.path.normpath(OutputDir))
        with open(f"{InputDir}", 'rb') as f:
            data: JSP = pickle.load(f)
            # print(self.speed)
            # for t in [0, 1, 2]:
            t = data.rddd
            # for s in range(1,self.speed+1):
            s = self.speed
            s0, sf, sp = [0,s,1]
            time = data.ProcessingTime[:, :, s0:sf:sp]
            energy = data.EnergyConsumption[:, :, s0:sf:sp]
            precedence = np.full((data.numJobs, data.numMchs), 0)

            replace_data = {
                "machines": data.numMchs,
                "jobs": data.numJobs,
                "Speed": s,
                "time": str(time.flatten()).replace(" ", ", "),
                "energy": str(energy.flatten()).replace(" ", ", ")
            }

            if t == 1:
                replace_data["releaseDate"] = str([int(data.ReleaseDueDate[job, 0]) for job in range(data.numJobs)]).replace(", ", " ")
                replace_data["dueDate"] = str([int(data.ReleaseDueDate[job, 1]) for job in range(data.numJobs)]).replace(", ", " ")
            elif t == 2:
                replace_data["releaseDate"] = str(data.ReleaseDueDate[:, :, 0].flatten()).replace(", ", " ")
                replace_data["dueDate"] = str(data.ReleaseDueDate[:, :, 1].flatten()).replace(", ", " ")

            for job in range(data.numJobs):
                for i, prioridad in enumerate(range(data.numMchs)):
                    precedence[job, data.Orden[job, prioridad]] = i

            replace_data["precedence"] = str(precedence.flatten()).replace(" ", ",")
            filedata = _read_text_resource(f"Minizinc/Types/RD/JSP/type{t}.dzn")
            # with open(f"./Minizinc/Types/RD/JSP/type{t}.dzn", "r", encoding="utf-8") as file:
                # filedata = file.read()
            for k, v in replace_data.items():
                filedata = filedata.replace("{" + k + "}", str(v))
            os.makedirs(f"{OutputDir}/", exist_ok=True)
            with open(f"{OutputDir}/{indexProblema}-{t}-{s}_{index}.dzn", "w+", encoding="utf-8") as new:
                new.write(filedata)

    def saveTaillardStandardFile(self, path):
        os.makedirs("/".join(path.split("/")[:-1]),exist_ok=True)
        with open(path, 'w+') as f:
            # Escribir el encabezado con el número de trabajos y máquinas
            f.write(f"Number of jobs: {self.numJobs}\n")
            f.write(f"Number of machines: {self.numMchs}\n\n")
            
            # Escribir la matriz de tiempos de procesamiento
            f.write("Processing times:\n")
            for job in range(self.numJobs):
                for machine_index in range(self.numMchs):
                    machine = self.Orden[job, machine_index]
                    processing_time = self.ProcessingTime[job, machine, 0]
                    f.write(f"{processing_time} ")
                f.write("\n")
            
            f.write("\n")

            # Escribir la matriz de consumo de energía
            f.write("Energy consumption:\n")
            for job in range(self.numJobs):
                for machine_index in range(self.numMchs):
                    machine = self.Orden[job, machine_index]
                    energy_consumption = self.EnergyConsumption[job, machine, 0]
                    f.write(f"{energy_consumption} ")
                f.write("\n")
            
            f.write("\n")

            # Escribir el orden de las máquinas para cada trabajo
            f.write("Machine order:\n")
            for job in range(self.numJobs):
                for machine_index in range(self.numMchs):
                    machine = self.Orden[job, machine_index]
                    f.write(f"{machine} ")
                f.write("\n")

    def select_speeds(self, speeds):
        if self.speed == len(speeds):
            return self
        new_object = copy.deepcopy(self)
        new_object.speed = len(speeds)
        new_object.ProcessingTime = new_object.ProcessingTime[:, :, speeds]
        new_object.EnergyConsumption = new_object.EnergyConsumption[:, :, speeds]
        new_object.generate_maxmin_objective_values()
        return new_object

    def change_rddd_type(self, new_rddd):
        if new_rddd == self.rddd:
            return self
        new_object = copy.deepcopy(self)
        new_object.rddd = new_rddd 
        if new_rddd == 0:
            if self.rddd != 0:
                del new_object.ReleaseDueDate
        elif new_rddd == 1:
            if self.rddd == 2:
                new_object.ReleaseDueDate = np.zeros((self.numJobs, 2), dtype=int)
                for job in range(self.numJobs):
                    new_object.ReleaseDueDate[job] = min(self.ReleaseDueDate[job, :, 0]), max(self.ReleaseDueDate[job, :, 1])
        elif new_rddd == 2:
            pass
        new_object.generate_maxmin_objective_values()
        return new_object

    def generate_maxmin_objective_values(self):
        max_makespan = sum([max(self.ProcessingTime[job, machine, :]) for job in range(self.numJobs) for machine in range(self.numMchs)])
        self.min_makespan = max([sum([min(self.ProcessingTime[job, machine, :]) for machine in range(self.numMchs)]) for job in range(self.numJobs)])
        self.max_min_makespan = max_makespan - self.min_makespan
        max_energy = sum([max(self.EnergyConsumption[job, machine, :]) for job in range(self.numJobs) for machine in range(self.numMchs)])
        self.min_energy = sum([min(self.EnergyConsumption[job, machine, :]) for job in range(self.numJobs) for machine in range(self.numMchs)])
        self.max_min_energy = max_energy - self.min_energy
        if self.rddd == 1:
            self.max_tardiness = sum([max(0, max_makespan - self.ReleaseDueDate[job, 1]) for job in range(self.numJobs)])
        elif self.rddd == 2:
            self.max_tardiness = np.sum([max(0, np.int64(max_makespan - self.ReleaseDueDate[job, machine, 1])) for job in range(self.numJobs) for machine in range(self.numMchs)])

    def norm_makespan(self, makespan):
        return (makespan - self.min_makespan) / self.max_min_makespan
    
    def norm_energy(self, energy):
        return (energy - self.min_energy) / self.max_min_energy if self.max_min_energy > 0 else 0
    
    def norm_tardiness(self, tardiness):
        return tardiness / self.max_tardiness if self.rddd > 0 else 0
    
    def objective_function_solution(self, solution):
        makespan = 0
        energy = 0
        tardiness = 0
        
        orders_done = [0] * self.numJobs
        available_time_machines = [0] * self.numMchs
        end_time_last_operations = [0] * self.numJobs
        
        tproc = [0] * self.numJobs
        for job, speed in zip(solution[::2], solution[1::2]):
            operation = orders_done[job]
            machine = self.Orden[job, operation]            
            
            end_time_last_operation = end_time_last_operations[job]
            available_time = available_time_machines[machine]
            
            if operation == 0:
                if self.rddd == 0:
                    release_date = 0
                elif self.rddd == 1:
                    release_date = self.ReleaseDueDate[job, 0]
                elif self.rddd == 2:
                    release_date = self.ReleaseDueDate[job, machine, 0]
            else:                
                if self.rddd == 2:
                    release_date = self.ReleaseDueDate[job, machine, 0]
                else:
                    release_date = available_time

            start_time = max(end_time_last_operation, available_time, release_date)
            end_time = start_time + self.ProcessingTime[job, machine, speed]

            if self.rddd == 2:
                tardiness += min(max(0, end_time - self.ReleaseDueDate[job, machine, 1]), self.ProcessingTime[job, machine, speed])
            energy += self.EnergyConsumption[job, machine, speed]
            if self.rddd == 1:
                tproc[job] += self.ProcessingTime[job, machine, speed]
            available_time_machines[machine] = end_time
            end_time_last_operations[job] = end_time
            orders_done[job] += 1
        
        makespan = max(end_time_last_operations)

        if self.rddd == 1:
            tardiness = sum(min(max(0, end_time - self.ReleaseDueDate[job, 1]), tproc[job]) for job, end_time in enumerate(end_time_last_operations))

        return self.norm_makespan(makespan) + self.norm_energy(energy) + self.norm_tardiness(tardiness), (makespan, energy, tardiness)

    def evalua_añadir_operacion(self, candidate, speed, makespan, energy, tardiness, orders_done, available_time_machines, end_time_last_operations, tproc, actualizacion):
        operation = orders_done[candidate]
        machine = self.Orden[candidate, operation]            
        
        end_time_last_operation = end_time_last_operations[candidate]
        available_time = available_time_machines[machine]
        
        if operation == 0:
            if self.rddd == 0:
                release_date = 0
            elif self.rddd == 1:
                release_date = self.ReleaseDueDate[candidate, 0]
            elif self.rddd == 2:
                release_date = self.ReleaseDueDate[candidate, machine, 0]
        else:                
            if self.rddd == 2:
                release_date = self.ReleaseDueDate[candidate, machine, 0]
            else:
                release_date = available_time

        start_time = max(end_time_last_operation, available_time, release_date)
        end_time = start_time + self.ProcessingTime[candidate, machine, speed]

        if self.rddd == 2:
            tardiness += min(max(0, end_time - self.ReleaseDueDate[candidate, machine, 1]), self.ProcessingTime[candidate, machine, speed])
        energy += self.EnergyConsumption[candidate, machine, speed]

        if actualizacion:
            available_time_machines[machine] = end_time
            end_time_last_operations[candidate] = end_time
            orders_done[candidate] += 1
            tproc[candidate] += self.ProcessingTime[candidate, machine, speed]

        makespan = makespan if end_time < makespan else end_time
        
        if self.rddd == 1:
            tardiness = sum(min(max(0, end_time - self.ReleaseDueDate[job, 1]), tproc[job]) for job, end_time in enumerate(end_time_last_operations))

        return self.norm_makespan(makespan) + self.norm_energy(energy) + self.norm_tardiness(tardiness), makespan, energy, tardiness

    def generate_schedule_image(self, schedule):
        pass

    def disjuntive_graph(self):
        vertex = list(range(self.numJobs * self.numMchs + 2))
        A = {v: [] for v in vertex}
        E = {v: [] for v in vertex}

        index = np.arange(1, self.Orden.size).reshape(self.numJobs, self.numMchs)

        for v in index[:, 0]:
            A[0].append(v)
        
        for v in index[:, -1]:
            A[v].append(self.numJobs * self.numMchs + 1)

        for job in range(self.numJobs):
            for machine in range(1, self.numMchs):
                A[index[job, machine - 1]].append(index[job, machine])
        aux = {m: [] for m in range(self.numMchs)}
        
        for job in range(self.numJobs):
            for machine in range(self.numMchs):
                aux[self.Orden[job, machine]].append(index[job, machine])
        
        for machine, vertex in aux.items():            
            for v, w in combinations(vertex, 2):
                A[v].append(w)
                A[w].append(v)
        return index, A, E
    
    def disjuntive_graph_solution(self, solution):
        graph = nx.Graph()
        graph.add_nodes_from([(0, {"valor": 0}), (self.numJobs * self.numMchs + 1, {"valor": 0})])
        
        orders_done = [0] * self.numJobs
        available_time_machines = [0] * self.numMchs
        end_time_last_operations = [0] * self.numJobs

        for job, speed in zip(solution[::2], solution[1::2]):

            operation = orders_done[job]
            machine = self.Orden[job, operation]
            valor = self.EnergyConsumption[job, machine, speed]   

            graph.add_node((job * self.numMchs + operation, {"valor": valor}))   
            if operation == 0:
                graph.add_edge((0, job * self.numMchs + operation))
            if operation == self.numMchs - 1:
                graph.add_edge((0, self.numJobs * self.numMchs + 1))            
            if operation > 0 and operation < self.numMchs - 1:
                graph.add_edge((job * self.numMchs + operation - 1, job * self.numMchs + operation))



#################################################################################
#                                                                               # 
#                                    FJSP                                       # 
#                                                                               #
#################################################################################


class FJSP(JSP):
    def __init__(self, jobs, machines, ProcessingTime=np.array([]), EnergyConsumption=np.array([]), ReleaseDateDueDate=np.array([]), Orden=np.array([]), AvailableMachines = np.array([])) -> None:

        super().__init__(jobs, machines, ProcessingTime, EnergyConsumption, ReleaseDateDueDate, Orden)
        self.available_machines = AvailableMachines
        
    def fill_random_values(self, speed, rddd, distribution, seed, tpm=[]):

        super().fill_random_values(speed, rddd, distribution, seed, tpm)
     
        self.available_machines = np.random.choice([0, 1], size=(self.numJobs, self.numMchs))

        # Asegurar al menos un 1 en cada columna
        for job in range(self.numJobs):
            if np.sum(self.available_machines[job, :]) == 0:
                columna_aleatoria = np.random.randint(0, self.numMchs)
                self.available_machines[job, columna_aleatoria] = 1

    # def savePythonFile(self, path):
    #     with open(path, 'wb') as f:
    #         pickle.dump(self, f)

    def saveJsonFile(self, path):
        self.JSP = {
            "nbJobs": list(range(self.numJobs)),
            "nbMchs": list(range(self.numMchs)),
            "speed": self.speed,
            "timeEnergy": [],
            "minMakespan": int(self.min_makespan),
            "minEnergy": int(self.min_energy),
            "maxMinMakespan": int(self.max_min_makespan),
            "maxMinEnergy": int(self.max_min_energy)
        }
        
        for job in range(self.numJobs):
            new = {
                "jobId": job,
                "operations": {},
                "available_machines": self.available_machines[job, : ].tolist()
            }

            #new["available_machines_prueba"] = self.available_machines[job, self.Orden[job] ].tolist() #for i in self.Orden[job]]

            for machine in self.Orden[job]:
                machine = int(machine)
                new["operations"][machine] = {"speed-scaling" : 
                                              [
                                                {"procTime" : int(proc),
                                                 "energyCons" : int(energy)
                                                }
                                                for proc, energy in zip(self.ProcessingTime[job, machine],self.EnergyConsumption[job, machine])
                                              ]
                                              }
                if self.rddd == 2:
                    new["operations"][machine]["release-date"] = int(self.ReleaseDueDate[job][machine][0])
                    new["operations"][machine]["due-date"] = int(self.ReleaseDueDate[job][machine][1])
            if self.rddd == 1:
                new["release-date"] = int(self.ReleaseDueDate[job][0])
                new["due-date"] = int(self.ReleaseDueDate[job][1])
            if self.rddd == 2:
                new["release-date"] = int(min(self.ReleaseDueDate[job, :, 0]))
                new["due-date"] = int(max(self.ReleaseDueDate[job, :, 1]))
            self.JSP["timeEnergy"].append(new)

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w+') as f:
            # Generamos el JSON con indentación normal
            json_str = json.dumps(self.JSP, indent=4)
            
            # Compresión selectiva: solo arrays de números simples
            def compress_simple_arrays(match):
                # Comprimir si el array contiene solo números y comas
                content = match.group(1)
                if re.match(r'^(\s*\d+\s*,)*\s*\d+\s*$', content):
                    # Eliminar espacios y saltos de línea
                    return '[' + re.sub(r'\s+', '', content) + ']'
                return match.group(0)  # Mantener como está si no es simple
            
            # Buscar arrays que puedan comprimirse
            json_str = re.sub(
                r'\[([\s\S]*?)\]', 
                compress_simple_arrays, 
                json_str,
                flags=re.DOTALL
            )
            
            f.write(json_str)

    def saveDznFile(self, InputDir, OutputDir,index):
        indexProblema = OutputDir.split("/")[-2]
        OutputDir = "/".join(OutputDir.split("/")[:-2])
        # indexProblema = os.path.basename(os.path.normpath(OutputDir))
        with open(f"{InputDir}", 'rb') as f:
            data: FJSP = pickle.load(f)
            # print(self.speed)
            # for t in [0, 1, 2]:
            t = data.rddd
            # for s in range(1,self.speed+1):
            s= self.speed
            s0, sf, sp = [0,s,1]
            time = data.ProcessingTime[:, :, s0:sf:sp]
            energy = data.EnergyConsumption[:, :, s0:sf:sp]
            precedence = np.full((data.numJobs, data.numMchs), 0)

            replace_data = {
                "machines": data.numMchs,
                "jobs": data.numJobs,
                "Speed": s,
                "time": str(time.flatten()).replace(" ", ", "),
                "energy": str(energy.flatten()).replace(" ", ", ")
            }
            if t == 1:
                replace_data["releaseDate"] = str([int(data.ReleaseDueDate[job, 0]) for job in range(data.numJobs)]).replace(" ", ",")
                replace_data["dueDate"] = str([int(data.ReleaseDueDate[job, 1]) for job in range(data.numJobs)]).replace(" ", ",")  
            elif t == 2:
                replace_data["releaseDate"] = str(data.ReleaseDueDate[:, :, 0].flatten()).replace(" ", ",")
                replace_data["dueDate"] = str(data.ReleaseDueDate[:, :, 1].flatten()).replace(" ", ",")

            for job in range(data.numJobs):
                for i, prioridad in enumerate(range(data.numMchs)):
                    precedence[job, data.Orden[job, prioridad]] = i
            replace_data["precedence"] = str(precedence.flatten()).replace(" ", ",")

            replace_data["available_machines"] = str(data.available_machines.flatten()).replace(" ", ", ")

            # with open(f"./Minizinc/Types/RD/FJSP/type{t}.dzn", "r", encoding="utf-8") as file:
            #     filedata = file.read()
            filedata = _read_text_resource(f"Minizinc/Types/RD/FJSP/type{t}.dzn")
            for kk, v in replace_data.items():
                filedata = filedata.replace("{" + kk + "}", str(v))

            os.makedirs(f"{OutputDir}/", exist_ok=True)

            with open(f"{OutputDir}/{indexProblema}-{t}-{s}_{index}.dzn", "w+", encoding="utf-8") as new:
                new.write(filedata)

    def saveTaillardStandardFile(self, path):
        os.makedirs("/".join(path.split("/")[:-1]),exist_ok=True)
        with open(path, 'w+') as f:
            # Escribir el encabezado con el número de trabajos y máquinas
            f.write(f"Number of jobs: {self.numJobs}\n")
            f.write(f"Number of machines: {self.numMchs}\n\n")
            
            # Escribir la matriz de tiempos de procesamiento
            f.write("Processing times:\n")
            for job in range(self.numJobs):
                # Almacenar todos los tiempos de esta fila
                tiempos = []
                for machine_index in range(self.numMchs):
                    machine = self.Orden[job, machine_index]
                    processing_time = self.ProcessingTime[job, machine, 0]
                    tiempos.append(str(processing_time))
                
                # Unir los tiempos con comas y escribirlos
                linea = ", ".join(tiempos)
                f.write(linea + "\n")
            
            f.write("\n")

            # Escribir la matriz de consumo de energía
            f.write("Energy consumption:\n")
            for job in range(self.numJobs):
                consumos = []
                for machine_index in range(self.numMchs):
                    machine = self.Orden[job, machine_index]
                    energy_consumption = self.EnergyConsumption[job, machine, 0]
                    consumos.append(str(energy_consumption))
                f.write(", ".join(consumos) + "\n")

            f.write("\n")

            # Escribir el orden de las máquinas para cada trabajo
            f.write("Machine order:\n")
            for job in range(self.numJobs):
                maquinas = []
                for machine_index in range(self.numMchs):
                    machine = self.Orden[job, machine_index]
                    maquinas.append(str(machine))
                f.write(", ".join(maquinas) + "\n")

            f.write("\n")

            f.write("Available machines:\n")
            for job in range(self.numJobs):
                disponibles = []
                for machine_index in range(self.numMchs):
                    disponibles.append(str(self.available_machines[job, machine_index]))
                f.write(", ".join(disponibles) + "\n")



class Generator:
    def __init__(self, json = False, dzn = False, taillard = False, savepath = "./", single_folder_output = False):
        self.json = json
        self.dzn = dzn
        self.taillard = taillard
        self.savepath = savepath
        self.single_folder_output = single_folder_output
        
    def generate_new_instance(self, jobs = 10, machines = 4, speed = 1, ReleaseDateDueDate = 0, distribution = "uniform" , seed = 0, tpm=[], instance_type = "JSP", size = 1):

        match instance_type:
            case "JSP":
                jsp_instance = JSP(jobs = jobs, machines = machines)
            case "FJSP":
                jsp_instance = FJSP(jobs = jobs, machines = machines)
        
        for index in range(1, size + 1):
            jsp_instance.fill_random_values(speed = speed, rddd = ReleaseDateDueDate, distribution = distribution, seed = seed,tpm = tpm)

            # Determinar el nombre de salida basado en `outputName` y los parámetros actuales
            problem_path = self.savepath.format(size = size, jobs =jobs, machines = machines, release_due_date = ReleaseDateDueDate,  speed_scaling = speed, distribution = distribution, seed=seed)
            
            if not (self.json or self.dzn or self.taillard): return jsp_instance
            
            j = str(jobs)
            m = str(machines)
            jm_path = str(j)+"_"+str(m)+"/"
            
            i = seed

            if self.single_folder_output:
                if self.json:
                    jsp_instance.saveJsonFile(problem_path + jm_path.split("/")[0] + f"_{j}x{m}_{i}.json")
                if self.dzn:
                    pkl_path = f"{problem_path}/" + jm_path.split("/")[0] + f"_{j}x{m}_{i}.pkl"
                    jsp_instance.savePythonFile(pkl_path)
                    jsp_instance.saveDznFile(pkl_path, problem_path + jm_path,index)#f"{j}x{m}_{i}")
                    os.remove(pkl_path)
                if self.taillard:
                    jsp_instance.saveTaillardStandardFile(problem_path + jm_path.split("/")[0] + f"_{j}x{m}_{i}.txt")
            else:
                if self.json:
                    jsp_instance.saveJsonFile(f"{problem_path}/JSON/" + jm_path.split("/")[0] + f"_{j}x{m}_{i}.json")
                if self.dzn:
                    pkl_path = f"{problem_path}/" + jm_path.split("/")[0] + f"_{j}x{m}_{i}.pkl"
                    jsp_instance.savePythonFile(pkl_path)
                    jsp_instance.saveDznFile(pkl_path,f"{problem_path}/DZN/" + jm_path,index)#f"{j}x{m}_{i}")
                    os.remove(pkl_path)
                if self.taillard:
                    jsp_instance.saveTaillardStandardFile(f"{problem_path}/TAILLARD/" + jm_path.split("/")[0] + f"_{j}x{m}_{i}.txt")

        return jsp_instance