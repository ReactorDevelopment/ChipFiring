from __future__ import annotations

import logging
import os.path
import time
import typing

import numpy as np
import sys

DEBUG = {"debug_out": False, "log_file": None, "snfRange": None, "snfPrepare": None}


loglevel = logging.INFO
if DEBUG["debug_out"]:
    loglevel = logging.DEBUG

logger = logging.getLogger(__name__)
handlers = [logging.StreamHandler(sys.stdout)]

if DEBUG["log_file"]:
    filePath = f"src/logs/{DEBUG['log_file']}"
    with open(filePath, "w") as file:
        file.write("===> Log File <===\n")
    handlers.append(logging.FileHandler(filePath))

logging.basicConfig(handlers=handlers, level=loglevel,
                    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")


class Utils:

    _logged = False

    @classmethod
    def setLogged(cls, lSet):
        cls._logged = lSet

    @classmethod
    def smithNormalForm(cls, matrix: np.ndarray):
        """Calculates the smith normal form of the given matrix"""
        smith: np.ndarray = matrix.copy()
        if DEBUG["snfPrepare"]:
            DEBUG["snfPrepare"](smith)
        if cls._logged:
            ops = LoggedMatrixOps
            # ops.endOps()
            # ops.startOps()
        else:
            ops = MatrixOps
        rangeMax = len(smith) if not DEBUG["snfRange"] else DEBUG["snfRange"][1]
        rangeMin = 0 if not DEBUG["snfRange"] else DEBUG["snfRange"][0]

        def minAij(s):
            """Find the minimum non-zero element below and to the right of matrix[s][s]"""
            element = [s, s]
            globalMin = float('inf')
            for i in range(s, rangeMax):
                for j in range(s, rangeMax):
                    if smith[i][j] != 0 and abs(smith[i][j]) <= globalMin:
                        element = [i, j]
                        globalMin = abs(smith[i][j])
            return element

        def isLone(s):
            """Checks if matrix[s][s] is the only non-zero in col s below matrix[s][s] and the only
            non-zero in row s to the right of matrix[s][s]"""
            if [smith[s][x] for x in range(s + 1, rangeMax) if smith[s][x] != 0] + [smith[y][s]
                    for y in range(s + 1, rangeMax) if smith[y][s] != 0] == []:
                return True
            else:
                return False

        def findNonDivisible(s):
            """Finds the first element which is not divisible by matrix[s][s]"""
            for x in range(s + 1, rangeMax):
                for y in range(s + 1, rangeMax):
                    if smith[x][y] % smith[s][s] != 0:
                        return x, y
            return None

        p = np.identity(rangeMax)
        q = np.identity(rangeMax)
        for s in range(rangeMin, rangeMax):
            while not isLone(s):
                # Get min location
                i, j = minAij(s)
                ops.exchangeRows(smith, p, s, i)
                ops.exchangeCols(smith, q, s, j)
                for x in range(s + 1, rangeMax):
                    if smith[x][s] != 0:
                        k = smith[x][s] // smith[s][s]
                        ops.addRows(smith, p, x, s, -k)
                for x in range(s + 1, rangeMax):
                    if smith[s][x] != 0:
                        k = smith[s][x] // smith[s][s]
                        ops.addCols(smith, q, x, s, -k)
                if isLone(s):
                    res = findNonDivisible(s)
                    if res:
                        x, y = res
                        ops.addRows(smith, p, s, x, 1)
                    else:
                        if smith[s][s] < 0:
                            ops.scaleRow(smith, p, s, -1)
            if smith[s][s] < 0:
                ops.scaleRow(smith, p, s, -1)
        return smith, p, q

    @classmethod
    def subSmith(cls, matrix: np.ndarray, depth: int = 0, minRange: int = 0, maxRange: int = None):
        if maxRange is None:
            maxRange = len(matrix)
        if depth > 0:
            def prepare(mtx):
                mimic = np.identity(len(matrix))
                LoggedMatrixOps.addRows(mtx, mimic, (maxRange-minRange)//2, (maxRange-minRange)//2 - 1)
                LoggedMatrixOps.addCols(mtx, mimic, (maxRange-minRange)//2 - 1, (maxRange-minRange)//2)

            DEBUG["snfPrepare"] = prepare
            partial1 = cls.subSmith(matrix, depth=depth-1, minRange=minRange, maxRange=(maxRange-minRange)//2)
            DEBUG["snfPrepare"] = None
            partial2 = cls.subSmith(partial1, depth=depth-1, minRange=(maxRange-minRange)//2, maxRange=maxRange)
            DEBUG["snfRange"] = None
            return Utils.smithNormalForm(partial2)[0]
        DEBUG["snfRange"] = (minRange, maxRange)
        return Utils.smithNormalForm(matrix)[0]

    @classmethod
    def coKernel(cls, matrix: np.ndarray, divisor: typing.Any | np.ndarray = None):
        """Returns the polynomial, invariant factors, and rank of the coKernel of the given matrix"""
        smith, p, q = cls.smithNormalForm(matrix)

        if not divisor:
            product = p
        else:
            product = np.matmul(p, divisor)
        infs = []
        invFactors: list[int] = []
        delModifier = 0
        for i in range(len(smith)):
            if smith[i][i] == 1 or np.all((smith[i] == 0)):
                product = np.delete(product, i + delModifier, axis=0)
                delModifier -= 1
                if np.all((smith[i] == 0)):
                    infs.append(float("inf"))
            else:
                invFactors.append(int(smith[i][i]))
        product = [np.atleast_1d(layer).tolist() for layer in product]
        if len(infs) > 0:
            product.append(infs)

        # polynomial, invariant factors, rank
        return product, invFactors, len(infs)

    @staticmethod
    def prettyCok(coKernel: tuple, compact=False):
        cokStr = ""
        mult = 1
        lastFactor = None
        if not compact:
            for factor in coKernel[1]:
                cokStr += f"\u2124_{factor} x "
        else:
            for factor in coKernel[1]:
                if lastFactor == factor:
                    mult += 1
                elif mult > 1:
                    cokStr += f"({mult})\u2124_{lastFactor} x "
                    mult = 1
                elif lastFactor is not None:
                    cokStr += f"\u2124_{lastFactor} x "
                lastFactor = factor
            if mult > 1 and lastFactor is not None:
                cokStr += f"({mult})\u2124_{lastFactor} x "
            elif lastFactor is not None:
                cokStr += f"\u2124_{lastFactor} x "

        if coKernel[2] > 0:
            cokStr += "\u2124" + (f"^{coKernel[2]}" if coKernel[2] > 1 else "")
        else:
            cokStr = cokStr[:-2]
        return cokStr


class MatrixOps:

    @staticmethod
    def exchangeRows(matrix: np.ndarray, mimic: np.ndarray, i: int, j: int):
        matrix[[i, j]] = matrix[[j, i]]
        mimic[[i, j]] = mimic[[j, i]]

    @staticmethod
    def exchangeCols(matrix: np.ndarray, mimic: np.ndarray, i: int, j: int):
        matrix[:, [i, j]] = matrix[:, [j, i]]
        mimic[:, [i, j]] = mimic[:, [j, i]]

    @staticmethod
    def addRows(matrix: np.ndarray, mimic: np.ndarray, i: int, j: int, scale=1):
        matrix[i, :] = matrix[i, :] + scale * matrix[j, :]
        mimic[i, :] = mimic[i, :] + scale * mimic[j, :]

    @staticmethod
    def addCols(matrix: np.ndarray, mimic: np.ndarray, i: int, j: int, scale=1):
        matrix[:, i] = matrix[:, i] + scale * matrix[:, j]
        mimic[:, i] = mimic[:, i] + scale * mimic[:, j]

    @staticmethod
    def scaleRow(matrix: np.ndarray, mimic: np.ndarray, i: int, scale):
        matrix[i, :] = scale * matrix[i, :]
        mimic[i, :] = scale * mimic[i, :]


class LoggedMatrixOps:

    stepNumber = None
    opNumber = None
    verbose = False

    @classmethod
    def startOps(cls):
        cls.stepNumber = 0
        cls.opNumber = 0

    @classmethod
    def endOps(cls):
        cls.stepNumber = None
        cls.opNumber = None

    @classmethod
    def printMatrix(cls, prev, current, opStr):
        cls.stepNumber += 1
        logStr = "" if cls.stepNumber is None else f"Step {cls.stepNumber}"
        for i in range(0, len(current)):
            logStr += "\n["
            for j in range(0, len(prev[0])):
                logStr += f"{prev[i][j]}, ".rjust(6, ' ')
            logStr += "]  "+(opStr if i == 0 else '-'*(len(opStr)-1)+">" if i == 1 else ' '*len(opStr))+"  ["
            for j in range(0, len(prev[0])):
                logStr += f"{current[i][j]}, ".rjust(6, ' ')
            logStr += "]"

        logger.info(logStr)

    @classmethod
    def exchangeRows(cls, matrix: np.ndarray, mimic: np.ndarray, i: int, j: int):
        prevMatrix = np.copy(matrix)
        matrix[[i, j]] = matrix[[j, i]]
        mimic[[i, j]] = mimic[[j, i]]
        cls.opNumber += len(matrix)
        if cls.verbose:
            cls.printMatrix(prevMatrix, matrix, f"R{i} <-> R{j}")

    @classmethod
    def exchangeCols(cls, matrix: np.ndarray, mimic: np.ndarray, i: int, j: int):
        prevMatrix = np.copy(matrix)
        matrix[:, [i, j]] = matrix[:, [j, i]]
        mimic[:, [i, j]] = mimic[:, [j, i]]
        cls.opNumber += len(matrix)
        if cls.verbose:
            cls.printMatrix(prevMatrix, matrix, f"C{i} <-> C{j}")

    @classmethod
    def addRows(cls, matrix: np.ndarray, mimic: np.ndarray, i: int, j: int, scale=1):
        prevMatrix = np.copy(matrix)
        matrix[i, :] = matrix[i, :] + scale * matrix[j, :]
        mimic[i, :] = mimic[i, :] + scale * mimic[j, :]
        cls.opNumber += len(matrix)
        if cls.verbose:
            cls.printMatrix(prevMatrix, matrix, f"R{i} -> R{i} + {scale}*R{j}")

    @classmethod
    def addCols(cls, matrix: np.ndarray, mimic: np.ndarray, i: int, j: int, scale=1):
        prevMatrix = np.copy(matrix)
        matrix[:, i] = matrix[:, i] + scale * matrix[:, j]
        mimic[:, i] = mimic[:, i] + scale * mimic[:, j]
        cls.opNumber += len(matrix)
        if cls.verbose:
            cls.printMatrix(prevMatrix, matrix, f"C{i} -> C{i} + {scale}*C{j}")

    @classmethod
    def scaleRow(cls, matrix: np.ndarray, mimic: np.ndarray, i: int, scale):
        prevMatrix = np.copy(matrix)
        matrix[i, :] = scale * matrix[i, :]
        mimic[i, :] = scale * mimic[i, :]
        cls.opNumber += len(matrix)
        if cls.verbose:
            cls.printMatrix(prevMatrix, matrix, f"R{i} -> {scale}*R{i}")
