from gi.repository import GObject
from pathlib import Path
from os.path import relpath
from .gloomhavenclass import GloomhavenClass
from .hexagonal_grid import HexagonDict

class BackupFileHandler(GObject.Object):
    """
    An abstract class to handle serialising some sort of Python object. A backup file is always created (.extension~)
    in case something crashes, and can be loaded back.
    For users of this class, before doing anything with it, you should
        - connect your function changing the object to BackupFileHandler.automatic_save
        - connect automatic_save.change_window_title to the function showing the path to the saved object.
    Can also flag a file as read-only. If this is the case, save and automatic_save can be called, but will have
    no effect.

    This function should be overloaded, as the abstract class can't know how to serialise an object.
    """
    @GObject.Signal
    def change_window_title(self):
        """
        Notification that the field displaying the name of the file (usually it's a window title) should be changed.
        Is emitted when modifying the object (automatic saves) or when the user saves the file.
        """
        pass

    def __init__(self, path_to_file: Path, extension: str, read_only = False):
        """
        A backup file handler should always be instantiated with a pointer to a file in a temporary directory.
        By default, this file
        - is in the "saved" state
        - does not have the right to be saved. This is because we do not want the user to save something in a
        temporary file (or else... poof), and is tracked by the boolean self.in_temporary_dir.
        """
        GObject.GObject.__init__(self)
        self.path_to_file = path_to_file
        self.is_saved = True # False if we should instead be writing on the backup file.
        self.in_temporary_dir = True
        self.extension = extension
        self.read_only = read_only

    def available_backup(self, target_file: str):
        """
        Return True if the given file has a backup that potentially could be loaded.
        """
        # The file was marked as saved internally but backup still exists.
        return Path(target_file).with_suffix(f".{self.extension}~").is_file()

    def open_new_file(self, new_path: str, load_backup = False, read_only = False):
        """
        Called when the user wants to open a file or a backup file.
        Return a deserialized python object corresponding to the data at the given location.
        This function will also close the previous file, discarding any unsaved changes (the backup file) and switch
        to the one at the given location. Furthermore, if a backup file exists at the new location but the user chose not
        to load it, then this backup file will be deleted.

        If something is to go wrong when deserializing the python object, then this function will return an uncaught error.
        However, in this case, it will still be pointing at the old file, as if the "Open New file" never happened.

        Note 1: this function will bug if load_backup is True but no backup exists. Always call self.available_backup()
        FIRST to make sure it exists.

        Must be overloaded and called by children classes (note: AFTER the deserialisation, so that if a deserialisation bug
        occurs, we do NOT switch to a new file).
        """
        # Close the old file
        self.close()
        # Load the new one, backup or real file.
        self.path_to_file = Path(new_path)
        self.in_temporary_dir = False
        self.read_only = read_only
        if load_backup:
            self.is_saved = False
        else:
            # Delete the backup, if it exists, at the given location. If this is the case, this means the user
            # said that he did NOT want to load the backup, so it is irrelevant.
            self.delete_backup_file()
            self.is_saved = True
        self.emit("change_window_title")

    def safe_to_close(self):
        """
        Should only be called by front-end users. Return True if the current object is saved and it is safe
        to close it.
        """
        return self.is_saved

    def automatic_save(self):
        """
        This function should be automatically called using a signal when the the object has been updated. Serialize
        the object to the backup file.

        Must be overloaded and called by children classes: the abstract class only takes care of changing the inner
        variables and doesn't actually do any serialisation.
        """
        if not self.read_only:
            self.is_saved = False
            self.emit("change_window_title")

    def save(self):
        """
        A true save, ie the user wants to write on the real file (not the backup .~ file).

        Must be overloaded and called by children classes: the abstract class only takes care of changing the inner
        variables and doesn't actually do any serialisation.
        """
        if not self.read_only:
            self.is_saved = True
            self.delete_backup_file()
            self.emit("change_window_title")

    def delete_backup_file(self):
        """
        Delete the backup file. This should happen when saving or when exiting the app.
        """
        backup = self.path_to_file.with_suffix(f".{self.extension}~")
        backup.unlink(missing_ok = True) # No error is raised is the backup file is missing.

    def new_path(self, new_path: str, read_only: bool = False):
        """
        This function should be called when the end-user specifies a path where he wants to save the .gml file.
        Also switch to this new path (ie further modifications will be saved to this location).
        """
        self.delete_backup_file()
        self.path_to_file = Path(new_path)
        self.in_temporary_dir = False
        self.read_only = read_only

    def get_window_title(self):
        """
        Return a string which shoule be displayed in the field giving the name of the file (usually it's a window title).
        It will something like "*file..." if the file is not saved, else it will be something like "file...".
        """
        prefix = ""
        if not self.is_saved and not self.read_only:
            # Read-only files can't be modified so they should never have the "*" prefix.
            prefix = "*"
        return prefix + str(self.path_to_file.name)

    def close(self):
        """
        Close nicely the file handler. This should always be called when the app is exited normally.
        """
        self.delete_backup_file()

    def no_save_path(self):
        """
        Return True if the file can't be saved as it is currently in a temporary directory: the user needs
        to give a valid path.
        """
        return self.in_temporary_dir

    def get_absolute_path(self, relative_path):
        """
        Given a relative path from the serialisation file, return the corresponding absolute path as a string.
        """
        return str((self.path_to_file / relative_path).resolve())

    def get_relative_path(self, absolutepath):
        """
        Given an absolute path, return its relative path to the serialisation file as a string.
        """
        # Apparently, this can't be done using pathlib, but is a one line with os.path
        return relpath(absolutepath, self.path_to_file.parent) # relpath assumes arguments are directories, hence the .parent


class GMLFileHandler(BackupFileHandler):
    """
    A class to handle the writing of a .gml file to disk and its associated backup.
    """
    def __init__(self, path_to_gml: Path, read_only = False):
        super().__init__(path_to_gml, "gml", read_only=read_only)

    def automatic_save(self, mainwindow):
        if not self.read_only:
            path_to_save = self.path_to_file.with_suffix(".gml~")
            mainwindow.current_class.set_path_to_gml(path_to_save)
            mainwindow.current_class.save()

        super().automatic_save()

    def save(self, custom_character: GloomhavenClass):
        """
        A true save, ie the user wants to write on the .gml file (not the backup .gml~ file).
        """
        if not self.read_only:
            custom_character.set_path_to_gml(self.path_to_file)
            custom_character.save()

        super().save()

    def open_new_file(self, new_path: str, load_backup=False, read_only=False):
        """
        Try to open the GML file. Raise uncaught error if the file couldn't be read.
        """
        path_to_gml = Path(new_path)
        if load_backup:
            path_to_gml = Path(new_path).with_suffix(".gml~")
        gloomhaven_class = GloomhavenClass.CreateFromFile(path_to_gml) # May raise an error, so that the next line isn't executed
        super().open_new_file(new_path, load_backup, read_only)
        return gloomhaven_class

class AoEFileHandler(BackupFileHandler):
    """
    A class to handle an .aoe file and its backup.
    """
    def __init__(self, path_to_file: Path, read_only=False):
        super().__init__(path_to_file, "aoe", read_only = read_only)

    def automatic_save(self, aoe_window):
        if not self.read_only:
            path_to_save = self.path_to_file.with_suffix(".aoe~")
            aoe_window.drawn_hexagons.serialize_aoe(path_to_save)

        super().automatic_save()

    def save(self, aoe_dict: HexagonDict):
        """
        A true save, ie the user wants to write on the .aoe file (not the backup .aoe~ file).
        """
        if not self.read_only:
            aoe_dict.serialize_aoe(self.path_to_file)

        super().save()

    def open_new_file(self, new_path: str, load_backup=False, read_only=False):
        """
        Try to open the AoE file. Raise uncaught error if the file couldn't be read.
        """
        path_to_aoe = Path(new_path)
        if load_backup:
            path_to_aoe = Path(new_path).with_suffix(".aoe~")
        new_hexagon_dict = HexagonDict.CreateFromFile(path_to_aoe) # May raise error so that the next line isn't executed
        super().open_new_file(new_path, load_backup, read_only)
        return new_hexagon_dict