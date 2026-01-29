import json
import base64
import io
import datetime
import uuid
import decimal
import pathlib

# Optional dependencies
try:
    import pydantic
except ImportError:
    pydantic = None

try:
    from PIL import Image
except ImportError:
    Image = None

class CactusJSONEncoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        self.asset_provider = kwargs.pop("asset_provider", None)
        super().__init__(*args, **kwargs)

    def default(self, obj):
        if pydantic and isinstance(obj, pydantic.BaseModel):
            try:
                return obj.model_dump()
            except AttributeError:
                return obj.dict()

        if Image and isinstance(obj, Image.Image):
            asset_id = f"gen_img_{uuid.uuid4().hex[:8]}"
            buffered = io.BytesIO()
            fmt = obj.format or "PNG"
            obj.save(buffered, format=fmt)
            
            if self.asset_provider:
                self.asset_provider(asset_id, buffered.getvalue(), f"image/{fmt.lower()}")
                return f"ccat://data/{asset_id}"

            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            return f"data:image/{fmt.lower()};base64,{img_str}"

        if isinstance(obj, bytes):
            if self.asset_provider:
                asset_id = f"gen_bin_{uuid.uuid4().hex[:8]}"
                self.asset_provider(asset_id, obj, "application/octet-stream")
                return f"ccat://data/{asset_id}"
            return base64.b64encode(obj).decode("utf-8")

        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        if isinstance(obj, datetime.timedelta):
            return obj.total_seconds()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        if isinstance(obj, pathlib.Path):
            return str(obj)
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, complex):
            return {"real": obj.real, "imag": obj.imag}

        try:
            import enum
            if isinstance(obj, enum.Enum):
                return obj.value
        except ImportError:
            pass

        try:
            import dataclasses
            if dataclasses.is_dataclass(obj):
                return dataclasses.asdict(obj)
        except ImportError:
            pass

        if hasattr(obj, "__dict__"):
            try:
                return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
            except TypeError:
                pass

        if hasattr(obj, "__slots__"):
            data = {}
            slots = obj.__slots__
            if isinstance(slots, str):
                slots = [slots]
            for key in slots:
                if not key.startswith("_"):
                    try:
                        data[key] = getattr(obj, key)
                    except Exception:
                        pass
            if data:
                return data

        try:
            return str(obj)
        except Exception:
            return super().default(obj)

def cactus_serialize(obj, asset_provider=None):
    """
    Serializes objects into primitives that can be passed to the frontend.
    Handles PIL images, Pydantic models, datetimes, and more.
    """
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj

    if pydantic and isinstance(obj, pydantic.BaseModel):
        try:
            return cactus_serialize(obj.model_dump(), asset_provider)
        except AttributeError:
            return cactus_serialize(obj.dict(), asset_provider)

    if Image and isinstance(obj, Image.Image):
        buffered = io.BytesIO()
        fmt = obj.format or "PNG"
        obj.save(buffered, format=fmt)
        if asset_provider:
            asset_id = f"gen_img_{uuid.uuid4().hex[:8]}"
            asset_provider(asset_id, buffered.getvalue(), f"image/{fmt.lower()}")
            return f"ccat://data/{asset_id}"
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/{fmt.lower()};base64,{img_str}"

    if isinstance(obj, bytes):
        if asset_provider:
            asset_id = f"gen_bin_{uuid.uuid4().hex[:8]}"
            asset_provider(asset_id, obj, "application/octet-stream")
            return f"ccat://data/{asset_id}"
        return base64.b64encode(obj).decode("utf-8")

    if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
        return obj.isoformat()
    if isinstance(obj, datetime.timedelta):
        return obj.total_seconds()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    if isinstance(obj, pathlib.Path):
        return str(obj)
    if isinstance(obj, set):
        return [cactus_serialize(i, asset_provider) for i in obj]
    if isinstance(obj, complex):
        return {"real": obj.real, "imag": obj.imag}

    try:
        import dataclasses
        if dataclasses.is_dataclass(obj):
            return cactus_serialize(dataclasses.asdict(obj), asset_provider)
    except:
        pass

    try:
        import enum
        if isinstance(obj, enum.Enum):
            return obj.value
    except:
        pass

    if isinstance(obj, dict):
        return {str(k): cactus_serialize(v, asset_provider) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [cactus_serialize(i, asset_provider) for i in obj]

    if hasattr(obj, "__dict__"):
        return {
            k: cactus_serialize(v, asset_provider)
            for k, v in vars(obj).items()
            if not k.startswith("_")
        }

    if hasattr(obj, "__slots__"):
        data = {}
        slots = obj.__slots__
        if isinstance(slots, str):
            slots = [slots]
        for key in slots:
            if not key.startswith("_"):
                try:
                    data[key] = cactus_serialize(getattr(obj, key), asset_provider)
                except Exception:
                    pass
        return data

    try:
        return str(obj)
    except:
        return None
