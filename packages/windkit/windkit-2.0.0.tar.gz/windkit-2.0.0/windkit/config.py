"""Creates a generic Configuration class object"""

import configparser
from datetime import datetime
import logging
from pathlib import Path
from pydantic import Field, ValidationError
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)
import platformdirs
import toml

logger = logging.getLogger(__name__)

APPNAME = "windkit"
APPAUTHOR = "DTU Wind Energy"

_CONFIG_FILE = (
    platformdirs.user_config_path(appname=APPNAME, appauthor=APPAUTHOR, roaming=True)
    / "./windkit_config.toml"
)
_OLD_INI_CONFIG_FILE = (
    platformdirs.user_config_path(appname=APPNAME, appauthor=APPAUTHOR, roaming=True)
    / "windkit.ini"
)


def _migrate_ini_to_toml(
    old_ini_path: Path,
    new_toml_path: Path,
    delete_old: bool = False,
    rename_ini_if_toml_exists: bool = False,
) -> None:
    """
    Detects if an old INI configuration file exists and converts its
    'user_data' section to the new TOML format.

    Optionally, if the new TOML file already exists, the old INI file is renamed
    to prevent accidental clobbering and allow user recovery.

    Optionally, if conversion is successful, the old INI file is deleted.

    Arguments
    ---------
    old_ini_path : Path
        The expected path to the old INI file.
    new_toml_path : Path
        The target path for the new TOML file.
    delete_old : bool
        If True, the old INI file will be deleted after successful migration.
        Defaults to False, meaning the old INI file will not be deleted.
    rename_ini_if_toml_exists : bool
        If True, the old INI file will be renamed if the new TOML file already
        exists, to prevent clobbering. Defaults to False, meaning the migration
        will not proceed if the new TOML file exists, and the old INI file will
        not be renamed.
    """
    if not old_ini_path.exists():
        logger.debug(f"No old INI file found at '{old_ini_path}'. No migration needed.")
        return

    logger.info(
        f"Old INI file found at '{old_ini_path}'. Attempting migration to TOML..."
    )

    if new_toml_path.exists():
        if not rename_ini_if_toml_exists:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        renamed_ini_path = (
            old_ini_path.parent
            / f"{old_ini_path.stem}_migrated_{timestamp}{old_ini_path.suffix}"
        )

        try:
            old_ini_path.rename(renamed_ini_path)
            logger.info(
                f"Existing TOML file found at '{new_toml_path}'. "
                f"Old INI file renamed to '{renamed_ini_path}' to prevent clobbering. "
                "Migration skipped."
            )
            return  # Exit function, as we've handled it by renaming
        except OSError as e:
            logger.error(
                f"Failed to rename old INI file '{old_ini_path}' to '{renamed_ini_path}': {e}. "
                "Aborting migration to prevent potential clobbering."
            )
            return

    parser = configparser.ConfigParser()
    try:
        parser.read(old_ini_path)
    except configparser.Error as e:
        logger.error(
            f"Error reading INI file '{old_ini_path}': {e}. Aborting migration."
        )
        return

    user_data = {}
    if "user_data" in parser:
        for key, value in parser["user_data"].items():
            user_data[key] = value
    else:
        logger.info(
            f"INI file '{old_ini_path}' found, but no '[user_data]' section. Skipping migration."
        )
        return

    if not user_data:
        logger.info(
            f"INI file '{old_ini_path}' found, but '[user_data]' section is empty. Skipping migration."
        )
        return

    try:
        # Save file to new format
        new_toml_path.parent.mkdir(parents=True, exist_ok=True)

        settings = Settings(**user_data)
        settings.model_config["toml_file"] = new_toml_path
        settings._save_config = True
        settings.save()
        logger.debug(f"Successfully converted '{old_ini_path}' to '{new_toml_path}'.")

        # Remove the old INI file after successful conversion
        if delete_old:
            old_ini_path.unlink()
            logger.debug(f"Old INI file '{old_ini_path}' deleted.")
    except ValidationError as e:
        logger.error(
            f"INI data validation failed for '{old_ini_path}': {e}. Aborting migration. INI file not deleted."
        )
    except Exception as e:
        logger.error(
            f"Error writing TOML file '{new_toml_path}': {e}. INI file not deleted."
        )


class Settings(BaseSettings):
    name: str = Field(..., description="The full name of the user")
    email: str = Field(..., description="The user's email address")
    institution: str = Field(..., description="The user's institution or company")

    _save_config: bool = False

    model_config = SettingsConfigDict(
        toml_file=_CONFIG_FILE,
        env_prefix="windkit_",
        extra="ignore",
    )

    # Add toml settings to end of default 4 sources
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            TomlConfigSettingsSource(settings_cls),
        )

    @classmethod
    def prompt_for_user_data(cls):
        print("Welcome! Please provide the following information:")
        name = input("Your Name: ")
        email = input("Your Email: ")
        institution = input("Your Institution: ")

        instance = cls(name=name, email=email, institution=institution)
        instance._save_config = True
        return instance

    @classmethod
    def load(cls):
        try:
            settings = cls()
            # Check if any of the user_data fields are still their default (None if not loaded)
            if not all(getattr(settings, field) for field in cls.model_fields):
                logger.debug("Missing at least one user_data field.")
                return cls.prompt_for_user_data()
            return settings
        except Exception:
            logger.debug("Error getting settings.")
            return cls.prompt_for_user_data()

    def save(self):
        if self._save_config:
            if not _CONFIG_FILE.parent.exists():
                _CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

            with _CONFIG_FILE.open("w") as f:
                toml.dump(self.model_dump(), f)

            self._save_config = False
            print(f"Configuration saved to {_CONFIG_FILE}.")


# Check if user has an OLD INI file and convert it if possible
_migrate_ini_to_toml(_OLD_INI_CONFIG_FILE, _CONFIG_FILE)
CONFIG = Settings.load()
# This is conditional on the user being prompted for the information
CONFIG.save()
