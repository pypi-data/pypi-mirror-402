################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2021-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
import logging
from numbers import Number

from scipy.stats import uniform

from autoai_libs.utils.intiger_ranges import uniform_integers

Category = str
NumberOrCategory = Number | Category


logger = logging.getLogger("autoai_libs")


class Parameter:
    def __init__(self, name=None):
        self.type = None
        self.name = name
        self.vmin = None
        self.vmax = None
        self.default = None
        self.list = None

    def get_range(self):
        return (self.vmin, self.vmax)

    def __repr__(self):
        default = None
        if self.__class__ is CategoricalParameter:
            if type(self.default) is str:
                default = self.list.index(self.default)
        else:
            if isinstance(self.default, type(self.vmin)):  # if type(self.default) == type(self.vmin):
                default = self.default
        if type(self.vmin) is int:
            cast = "int("
            close = ")"
        elif type(self.vmin) is float:
            cast = "float("
            close = ")"
        else:
            cast = ""
            close = ""
        if type(default) is int:
            cast_default = "int("
            close_default = ")"
        elif type(default) is float:
            cast_default = "float("
            close_default = ")"
        else:
            cast_default = ""
            close_default = ""
        # return '('+str(self.vmin) + ', ' + str(self.vmax) + ', '+ str(default) +')'
        return (
            "("
            + cast
            + str(self.vmin)
            + close
            + ", "
            + cast
            + str(self.vmax)
            + close
            + ", "
            + cast_default
            + str(default)
            + close_default
            + ")"
        )

    def keep_sorted(self):
        pass

    def set_default(self, default):
        self.default = default
        self.keep_sorted()

    def get_min_max_default_tuple(self):
        return self.vmin, self.vmax, self.default

    def get_as_values_list(self, size=None):
        plist = []
        return plist

    def add(self, value):
        if self.vmin is None and self.vmax is None:
            self.vmin = value
            self.vmax = value
        elif self.vmin > value:
            self.vmin = value
        elif self.vmax < value:
            self.vmax = value

    def surround(self, value):  # allows us to encode values that are not in the search range
        return

    def encode(self, value):  # return the value for float and int, index otherwise
        return value

    def decode(self, value):  # return the value for float and int, use value as index otherwise
        return value

    def get_type(self):
        return self.type

    def get_invocation(self):
        s = self.__class__.__name__ + "("
        if hasattr(self, "list"):
            s += "values=" + str(self.list) + ","
        if hasattr(self, "vmin"):
            s += "vmin=" + str(self.vmin) + ","
        if hasattr(self, "vmax"):
            s += "vmax=" + str(self.vmax) + ","
        if hasattr(self, "default"):
            quot = ""
            if type(self.default) is str:
                quot = "'"
            s += "default=" + quot + str(self.default) + quot + ","
        s = s[:-1] + ")"
        return s

    @classmethod
    def construct_from_range(cls, name=None, min_max_default=None, categories=None):
        if type(min_max_default) is tuple:
            vmin, vmax, default = min_max_default
        else:
            return NullParameter(name=name)
        if categories is not None:
            return CategoricalParameter(name=name, values=categories, default=default)
        if type(vmin) is float:
            return FloatParameter(name=name, vmin=vmin, vmax=vmax, default=default)
        if type(vmin) is bool:
            return BooleanParameter(name=name, vmin=vmin, vmax=vmax, default=default)
        if type(vmin) is int:
            return IntegerParameter(name=name, vmin=vmin, vmax=vmax, default=default)
        raise (TypeError("No parameter_type for type " + str(type(vmin))))


class NullParameter(Parameter):
    def __init(self, name=None):
        super().__init__(name=name)


class BooleanParameter(Parameter):
    def __init__(self, name=None, vmin=False, vmax=True, default=None):
        super().__init__(name)
        self.name = name
        self.type = bool
        self.vmin = vmin
        self.vmax = vmax
        self.default = default

    def get_as_values_list(self, size=None):
        plist = []
        if self.default is not None:
            plist.insert(0, self.default)
        if self.vmax not in plist:
            plist.insert(0, self.vmax)
        if self.vmin not in plist:
            plist.insert(0, self.vmin)
        return plist

    def encode(self, value):
        if value == self.vmin:
            return 0
        if value == self.vmax:
            return 1

    def decode(self, value):
        if value == 0:
            return self.vmin
        if value == 1:
            return self.vmax


class IntegerParameter(Parameter):
    def __init__(self, name=None, vmin=0, vmax=1, default=None):
        super().__init__(name)
        self.name = name
        self.type = int
        self.vmin = vmin
        self.vmax = vmax
        self.default = default

    def get_as_values_list(self, size=None):
        plist = uniform_integers(self.vmin, self.vmax, size)
        return plist


class FloatParameter(Parameter):
    def __init__(self, name=None, vmin=0.0, vmax=1.0, default=None):
        super().__init__(name)
        self.name = name
        self.type = float
        self.vmin = vmin
        self.vmax = vmax
        self.default = default

    def get_as_values_list(self, size=None):
        plist = uniform.rvs(loc=self.vmin, scale=self.vmax - self.vmin, size=size)
        return plist


class CategoricalParameter(Parameter):
    def __init__(self, name=None, values=None, default=None):
        super().__init__(name)
        self.name = name
        self.type = int
        self.vmin = None
        self.vmax = None
        self.list = []
        self.outliers = []
        self.default = default
        self.extend(values)

    def get_as_values_list(self, size=None):
        return list(self.list)

    def keep_sorted(self):
        # sort list alphabetically, but put default at end
        if self.default is not None:
            if len(self.list) > 0:
                alist = []
                try:
                    for el in sorted(self.list):
                        if el != self.default:
                            alist.append(el)
                except Exception as e:
                    logger.warning("handled exception ", exc_info=e)

                alist.append(self.default)
                self.list = alist
                self.vmax = int(len(alist) - 1)

    def add(self, value):
        # FIXME this is a hack to remove spurious empty strings, leaving no way to have an intentionally empty string
        if value == "":
            return
        if value not in self.list:
            self.list.append(value)
            if self.vmin is None:
                self.vmin = 0
                self.vmax = 0
            else:
                self.vmax += 1
            self.keep_sorted()

    def extend(self, value_or_iterable=None):
        try:
            for v in value_or_iterable:
                self.add(v)
        except:
            self.add(value_or_iterable)
        self.keep_sorted()

    def __repr__(self):
        return super().__repr__() + " # " + str(self.list)

    def get_min_max_default_tuple(self):
        return self.vmin, self.vmax, self.vmax

    def surround(self, value):
        if value not in self.list:
            if value not in self.outliers:
                self.outliers.append(value)
                # fixme these lists might need to be maintained against subsequent add()

    def encode(self, value):
        if value in self.list:
            return self.list.index(value)
        else:
            idx = self.outliers.index(value)
            return len(self.list) + idx


def get_param_dist_from_objects(param_objects: dict[str, Parameter], size: int = 10) -> list[NumberOrCategory]:
    param_dist: dict[str, list[NumberOrCategory]] = {}
    for pname, parameter in param_objects.items():
        if parameter.__class__ is not NullParameter:
            param_dist[pname] = parameter.get_as_values_list(size=size)
    return param_dist


def get_param_ranges_from_objects(param_objects=None):
    param_ranges = []
    param_categorical_indices = []
    for pname, parameter in param_objects.items():
        if parameter.__class__ is NullParameter:
            continue
        elif parameter.__class__ is CategoricalParameter:
            param_ranges[pname] = parameter.list
            param_categorical_indices[pname] = parameter.get_min_max_default_tuple()
        else:
            param_ranges[pname] = parameter.get_min_max_default_tuple()
    return param_ranges, param_categorical_indices
