"""
deep_logger.py

Logger haute performance basé sur sys._getframe
Aucune dépendance externe
"""

import sys
import datetime
import threading
from types import FrameType


def _short_repr(value) -> str:
    try:
        cls = value.__class__.__name__
        return f"<{cls}>"
    except Exception:
        return "<object>"


def _long_repr(value) -> str:
    str_value = repr(value)
    if " object at" in str_value:
        return f"{str_value[:str_value.index(' object at')]}>"
    return str_value


class Logger:
    __slots__ = ("name", "log_args", "log_attrs", "log_private_attrs", "max_depth")

    def __init__(
        self,
        name: str | None = None,
        log_args: bool = True,
        log_attrs: bool = True,
        log_private_attrs: bool = False,
        max_depth: int = -1,
    ):
        self.name = name or "NamelessLogger"
        self.log_args = log_args
        self.log_attrs = log_attrs
        self.log_private_attrs = log_private_attrs
        self.max_depth = max_depth

    def log(self, message: str, level: str = "INFO") -> None:
        context = self._get_call_context()
        formatted = self._format_message(
            message=message,
            level=level,
            context=context,
        )
        self._output(formatted)

    def _get_call_context(self) -> dict:
        frame = self._find_caller_frame()
        root_module = frame.f_globals.get("__name__") if frame else None
        if frame is None:
            return self._empty_context()
        code = frame.f_code
        module_name = frame.f_globals.get("__name__", "<unknown>")
        return {
            "module": module_name,
            "file": code.co_filename,
            "line": frame.f_lineno,
            "function": code.co_name,
            "thread": threading.current_thread().name,
            "context_chain": self._build_context_chain(frame, root_module),
        }

    def _build_context_chain(self, frame: FrameType, root_module: str | None) -> list[dict]:
        """
        Recursively trace :
        - frames (functions/methods)
        - parent objects (via instance relationships)
        """
        chain: list[dict] = []
        visited_instances: set[int] = set()
        depth = 0
        instance = None

        current_frame = frame
        while current_frame:
            if self.max_depth != -1 and depth >= self.max_depth:
                break
            module_name = current_frame.f_globals.get("__name__")
            if root_module and module_name != root_module:
                break
            entry: dict = {
                "module": module_name,
                "function": current_frame.f_code.co_name,
                "args": self._get_function_arguments(current_frame),
            }
            instance = current_frame.f_locals.get("self")
            if instance is not None:
                entry["class"] = instance.__class__.__name__
                entry["attrs"] = self._get_instance_attrs(instance)
            chain.append(entry)
            depth += 1
            current_frame = current_frame.f_back

        for entry in chain:
            instance = None
            if "class" in entry:
                instance = frame.f_locals.get("self")
                break

        if instance is not None:
            current = instance
            while current and id(current) not in visited_instances:
                if self.max_depth != -1 and depth >= self.max_depth:
                    break
                visited_instances.add(id(current))
                parent = self._find_parent_instance(current)
                if parent is None:
                    break
                if root_module and parent.__class__.__module__ != root_module:
                    break
                chain.append(
                    {"class": parent.__class__.__name__, "attrs": self._get_instance_attrs(parent)}
                )
                depth += 1
                current = parent

        return chain

    def _empty_context(self) -> dict:
        return {
            "module": "<unknown>",
            "file": "<unknown>",
            "line": -1,
            "function": "<unknown>",
            "class": None,
            "thread": threading.current_thread().name,
        }

    def _get_instance_attrs(self, instance) -> dict | None:
        if not self.log_attrs:
            return None
        try:
            attrs = vars(instance)
        except Exception:
            return None
        result = {}
        for name, value in attrs.items():
            if name.startswith("_") and not self.log_private_attrs:
                continue
            if hasattr(value, "__dict__"):
                result[name] = _short_repr(value)
            else:
                result[name] = _long_repr(value)
        return result or None

    def _walk_instance_parents(
        self, instance, chain: list, visited: set, root_module: str | None, depth: int
    ) -> None:
        """
        Trace parent objects by following instance references.
        """
        current = instance
        while current and id(current) not in visited:
            if self.max_depth != -1 and depth >= self.max_depth:
                break
            visited.add(id(current))
            module_name = current.__class__.__module__
            if root_module and module_name != root_module:
                break
            entry = {
                "class": current.__class__.__name__,
                "attrs": self._get_instance_attrs(current),
            }
            depth += 1
            chain.append(entry)
            parent = self._find_parent_instance(current)
            current = parent

    def _find_parent_instance(self, instance):
        """
        Safe heuristic:
        - look for an attribute that is an instance of another user class
        - ignore builtins
        """
        try:
            attrs = vars(instance)
        except Exception:
            return None
        for value in attrs.values():
            if (
                hasattr(value, "__class__")
                and value.__class__.__module__ == instance.__class__.__module__
                and not isinstance(value, (int, str, float, bool, tuple, list, dict, set))
            ):
                if value is instance:  # prevent self-referencing
                    continue
                return value
        return None

    def _find_caller_frame(self) -> FrameType | None:
        try:
            frame = sys._getframe(2)
        except ValueError:
            return None
        logger_module = __name__
        while frame:
            module_name = frame.f_globals.get("__name__")
            if module_name != logger_module:
                return frame
            frame = frame.f_back
        return None

    def _get_function_arguments(self, frame) -> dict | None:
        if not self.log_args:
            return None
        code = frame.f_code
        locals_ = frame.f_locals
        arg_names = code.co_varnames[: code.co_argcount]
        args = {}
        for name in arg_names:
            if name == "self":
                continue
            if name in locals_:
                try:
                    args[name] = _long_repr(locals_[name])
                except Exception:
                    args[name] = "<unreprable>"
        return args if args else None

    def _get_class_name(self, frame: FrameType) -> str | None:
        locals_ = frame.f_locals
        if not locals_:
            return None
        first_key = next(iter(locals_), None)
        if not first_key:
            return None
        instance = locals_.get(first_key)
        if instance is None:
            return None
        try:
            return instance.__class__.__name__
        except Exception:
            return None

    def _get_class_attributes(self, frame) -> dict | None:
        if not self.log_attrs:
            return None
        locals_ = frame.f_locals
        if not locals_:
            return None
        instance = locals_.get("self")
        if instance is None:  # if not self in locals we assume we're not in a class
            return None
        try:
            attrs = vars(instance)
        except Exception:
            return None
        if not attrs:
            return None
        result = {}
        for name, value in attrs.items():
            if name.startswith("_") and not self.log_private_attrs:
                continue
            try:
                result[name] = _short_repr(value)
            except Exception:
                result[name] = "<unreprable>"
        return result if result else None

    def _format_message(self, message: str, level: str, context: dict) -> str:
        timestamp = datetime.datetime.now().isoformat(timespec="milliseconds")
        lines: list[str] = []
        lines.append(f"[{timestamp}] [{level}] [thread={context['thread']}]")  # Header
        lines.append(f"│ module: {context['module']}")
        lines.append("│ call stack:")
        chain = context.get("context_chain", [])
        if not chain:
            lines.append("│ └─ <no call context>")
        else:
            # Display from root (module-level) to logger call
            display_chain = list(reversed(chain))
            last_index = len(display_chain) - 1
            for idx, entry in enumerate(display_chain):
                is_last = idx == last_index
                branch = "└─" if is_last else "├─"
                vertical = "   " if is_last else "│  "
                line = "│ " + branch + " "  # Build function / class representation
                if "class" in entry:
                    line += entry["class"] + "."
                line += entry.get("function", "<unknown>")
                args = entry.get("args")
                if args:
                    args_str = ", ".join(f"{k}={v}" for k, v in args.items())
                    line += f"({args_str})"
                lines.append(line)
                attrs = entry.get("attrs")  # Attributes block
                if attrs:
                    lines.append("│ " + vertical + "attrs:")
                    for key, value in attrs.items():
                        lines.append("│ " + vertical + f"  {key} = {value}")
        lines.append("│")  # Message block (always last)
        lines.append("└─ message:")
        lines.append(f"   {message}")
        return "\n".join(lines)

    def _output(self, formatted_message: str) -> None:
        print(formatted_message)
