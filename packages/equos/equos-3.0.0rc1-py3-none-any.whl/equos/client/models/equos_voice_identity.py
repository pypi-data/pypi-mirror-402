from enum import Enum


class EquosVoiceIdentity(str, Enum):
    ACHERNAR = "Achernar"
    ACHIRD = "Achird"
    ALGENIB = "Algenib"
    ALGIEBA = "Algieba"
    ALNILAM = "Alnilam"
    AOEDE = "Aoede"
    AUTONOE = "Autonoe"
    CALLIRRHOE = "Callirrhoe"
    CHARON = "Charon"
    DESPINA = "Despina"
    ENCELADUS = "Enceladus"
    ERINOME = "Erinome"
    FENRIR = "Fenrir"
    GACRUX = "Gacrux"
    IAPETUS = "Iapetus"
    KORE = "Kore"
    LAOMEDEIA = "Laomedeia"
    LEDA = "Leda"
    ORUS = "Orus"
    PUCK = "Puck"
    PULCHERRIMA = "Pulcherrima"
    RASALGETHI = "Rasalgethi"
    SADACHBIA = "Sadachbia"
    SADALTAGER = "Sadaltager"
    SCHEDAR = "Schedar"
    SULAFAT = "Sulafat"
    UMBRIEL = "Umbriel"
    VINDEMIATRIX = "Vindemiatrix"
    ZEPHYR = "Zephyr"
    ZUBENELGENUBI = "Zubenelgenubi"

    def __str__(self) -> str:
        return str(self.value)
