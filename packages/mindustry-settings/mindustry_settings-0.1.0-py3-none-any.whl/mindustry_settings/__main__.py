from pathlib import Path

from src.mindustry_settings.settings import MindustrySettings

if __name__ == "__main__":
    settings = MindustrySettings(Path("../phos.bin"))
    settings.set_value("uuid", "phosphophyllite")
    settings.write_to_disk()

    settings.load()

    print(settings.get_string("uuid"))

    # output_stream = DataOutputStream(Path("../lorem.bin").open("wb"))
    # output_stream.write_int(1)
    # output_stream.write_str("uuid")
    # output_stream.write_byte(4)
    # output_stream.write_str("phosphophyllite")
