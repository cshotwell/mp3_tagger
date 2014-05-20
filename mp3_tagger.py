#!/usr/bin/env python3

import os
import webbrowser
import npyscreen
import album_art_utils
from mp3_track import MP3Track
from file_utils import get_mp3_files

# TODO:
# - Look into best-guess auto-tagging based existing tag information leveraging some third-party service.
# - Add support for x/y disc number frame.
# - Add support for different file renaming patterns.
# - Support genre int -> genre mapping.
# - Add mouse support so you don't have to use tab and arrow keys so much.
# - Add some sort of indicator that tags have been changed, but not saved.
# - Sort by track number if possible and and auto-track numbering. Add a way to re-order list before auto-numbering.
#   Maybe do this in a popup window.
# - When selecting a titled widget, the title turns white. See if it is possible to stop this from happening.
# - Figure out how to to put boxes around certain groups of widgets to add polish to the UI.
# - Check out this page for more tags to support. It is much better than the actual official spec sheet.
#   http://help.mp3tag.de/main_tags.html
# - When looking at frames to get their values, remember that the unary operator helps parse a lot of things out. This
#   means I won't have to use regular expressions on the frame's text attribute.
#   See the Mutagen frame docs: http://mutagen.readthedocs.org/en/latest/api/id3_frames.html#id3v2-3-4-frames
# - As development on npyscreen continues, in the near future, it may not be necessary to access wrapped entry_widgets
#   of titled widgets. For example, there were some recent developments wtih change listeners, where the title wrapper
#   proxies calls.
# - The developer of npyscreen is pretty active and is will answer questions.
#   See: https://groups.google.com/forum/?fromgroups#!forum/npyscreen


class Field:
    """ An input field made up of a selection checkbox, a title, and an entry widget. Each field is associated with a
    getter method and setter method. These methods are to read and write the field's value when applied on an object
    instance.
    """

    # The width of a checkbox widget before its title text.
    CHECKBOX_BUILT_IN_WIDTH = 6

    # The number of spaces to the right of a checkbox title the entry field should go.
    CHECKBOX_RIGHT_MARGIN = 2

    # The text to display in entry_widget when multiple tracks with different values are selected at the same time.
    MULTIPLE_VALUES_TEXT = "Multiple Values"

    def __init__(self, name, toggle, getter, setter, parent_form):
        """Create a new field and add it to a parent form.

        :param name: The field label.
        :type name: str

        :param toggle: Whether or the field is a toggle checkbox (true) or a text entry field (false).
        :type toggle: bool

        :param getter: The name of the getter method to associate this field with.
        :type getter: str

        :param setter: The name of the setter method to associate this field with.
        :type setter: str

        :param parent_form: The form this field should be added to.
        :type parent_form: str
        """

        self.toggle = toggle
        self.getter = getter
        self.setter = setter

        # TODO: Figure out why the value text sometimes disappears/gets covered up if I don't specify max_width.
        checkbox_max_width = len(name) + Field.CHECKBOX_BUILT_IN_WIDTH
        field_relx = checkbox_max_width + Field.CHECKBOX_RIGHT_MARGIN
        self.checkbox = parent_form.add(npyscreen.CheckBox, max_width=checkbox_max_width, name=name)

        # The value of rely automatically increments. Subtract one so the entry widget is on the same line.
        parent_form.nextrely -= 1

        if toggle:
            self.entry_widget = parent_form.add(npyscreen.CheckBox, relx=field_relx)
        else:
            self.entry_widget = parent_form.add(npyscreen.Textfield, relx=field_relx)

    def set_visibility(self, is_visible):
        """Set the visibility of the field.

        :param is_visible: True to set the field visible, false to hide it.
        :type is_visible: bool
        """

        hidden = not is_visible

        self.checkbox.hidden = hidden
        self.entry_widget.hidden = hidden

    def clear(self):
        """Clear the field's value."""

        self.checkbox.value = False

        if self.toggle:
            self.entry_widget.value = False
            self.entry_widget.name = ""
        else:
            self.entry_widget.value = ""

        self.checkbox.update()
        self.entry_widget.update()

    def is_selected(self):
        """Whether or not the field is selected.

        :returns: True if the field is selected, false otherwise.
        :rtype: bool
        """

        return self.checkbox.value

    def update_value_from_tracks(self, mp3_tracks):
        """Update the entry widget's value based on a set of selected tracks. If all tracks have the same value for
        this field associated getter, then the field will show that value. Otherwise, it will indicate multiple values.

        :param mp3_tracks: A list of selected tracks.
        :type mp3_tracks: set
        """

        # TODO: This method could probably be optimized if using some set differences, intersection, etc.

        self.clear()

        if len(mp3_tracks) == 0:
            return

        # Grab a random track from the set to start with.
        random_track = mp3_tracks.pop()
        mp3_tracks.add(random_track)
        # Set that track's value as the entry field's value.
        self.entry_widget.value = getattr(random_track, self.getter)()
        # Loop through all of tracks and change the entry field value to indicate multiple values of necessary.
        for track in mp3_tracks:
            if self.entry_widget.value != getattr(track, self.getter)():
                if self.toggle:
                    self.entry_widget.name = Field.MULTIPLE_VALUES_TEXT
                else:
                    self.entry_widget.value = Field.MULTIPLE_VALUES_TEXT
                break

        # Refresh the UI.
        self.entry_widget.update()

    def apply_value_to_track(self, mp3_track):
        """Apply the entry widget value to a track using this field's associated setter.

        Note: This does not call save on the track. The change will not persist unless the track is saved.

        :param mp3_track: The MP3Track to to apply the entry widget value to.
        :type mp3_track: MP3Track
        """

        getattr(mp3_track, self.setter)(self.entry_widget.value)


class TrackEditorForm(npyscreen.FormBaseNew):
    """The main form that includes all widgets that make up the UI."""

    # The height of the list of tracks. If there are more tracks than can fit, a scrolling affordance appears.
    TRACK_LIST_HEIGHT = 10

    # The color scheme of the buttons.
    BUTTON_COLOR = "LABEL"

    def __init__(self, *args, **keywords):
        """Override default constructor in order to declare member variables to stop my IDE from complaining."""

        self.folder_input = None
        self.load_button = None
        self.file_list = None
        self.select_all_files_button = None
        self.save_button = None
        self.rename_button = None
        self.album_art_search_box = None
        self.search_button = None
        self.debug_button = None

        # A set of editor fields including a checkbox and an entry widget.
        self.fields = set()

        # A map of filenames to their corresponding mp3_track wrappers.
        self.mp3_tracks = {}

        # A set of the selected mp3_track wrappers.
        self.selected_mp3_tracks = set()

        # Call super after initializing member variables as super calls self.create() and we do not want to overwrite.
        super().__init__(*args, **keywords)

    def create(self):
        """Called when the form's widgets should be initialized and added."""

        self.folder_input = self.add(npyscreen.TitleFilename, name="Enter folder using the tab key for auto-complete:",
                                     use_two_lines=True, begin_entry_at=0)
        self.folder_input.set_value(os.getcwd())

        self.load_button = self.add(npyscreen.ButtonPress, name="[Open Folder]", color=TrackEditorForm.BUTTON_COLOR)
        self.load_button.whenPressed = self.update_file_list

        self.nextrely += 1

        # TODO: Put a constant size box around this because variable gap between list and select all button is ugly.
        self.file_list = self.add(npyscreen.TitleMultiSelect, name="Use the space key to select files to edit:",
                                  use_two_lines=True, begin_entry_at=0, max_height=TrackEditorForm.TRACK_LIST_HEIGHT,
                                  scroll_exit=True)
        self.file_list.when_value_edited = self.on_file_list_selection_change
        # I hate all the monkey patching done here and below, but it less code and cleaner than extending each widget.
        self.file_list.entry_widget.display_value = self.format_file_list_line

        self.select_all_files_button = self.add(npyscreen.ButtonPress, name="[Select All Files]",
                                                color=TrackEditorForm.BUTTON_COLOR)
        self.select_all_files_button.whenPressed = self.select_all_files

        self.nextrely += 1

        self.fields.add(Field("Title:", False, "get_title", "set_title", self))
        self.fields.add(Field("Artist:", False, "get_artist", "set_artist", self))
        self.fields.add(Field("Album Artist:", False, "get_album_artist", "set_album_artist", self))
        self.fields.add(Field("Album:", False, "get_album", "set_album", self))
        self.fields.add(Field("Genre:", False, "get_genre", "set_genre", self))
        self.fields.add(Field("Year:", False, "get_year", "set_year", self))
        self.fields.add(Field("Track:", False, "get_track", "set_track", self))
        self.fields.add(Field("Comment:", False, "get_comments", "add_comment", self))
        self.fields.add(Field("Part of Compilation:", True, "get_part_of_compilation", "set_part_of_compilation", self))

        self.save_button = self.add(npyscreen.ButtonPress, name="[Save Tags]", color=TrackEditorForm.BUTTON_COLOR)
        self.save_button.whenPressed = self.save_entries_to_tracks
        self.rename_button = self.add(npyscreen.ButtonPress, name="[Rename Files Based On Tags]", color=TrackEditorForm.BUTTON_COLOR)
        self.rename_button.whenPressed = self.rename_files

        self.nextrely += 1

        # TODO: Clean this search UI and code up. Launch a popup with a list of launchable image URLs to choose from.
        self.album_art_search_box = self.add(npyscreen.TitleText, name="Album Art Query:", use_two_lines=False,
                                             begin_entry_at=17)
        self.search_button = self.add(npyscreen.ButtonPress, name="[Search]", relx=18,
                                      color=TrackEditorForm.BUTTON_COLOR)
        self.search_button.whenPressed = self.lookup_album_art

        self.set_list_and_editor_visibility(False)

        # TODO: Uncomment this out to enable debugging button.
        # self.debug_button = self.add(npyscreen.ButtonPress, name="[Debug]", color=TrackEditorForm.BUTTON_COLOR)
        # self.debug_button.whenPressed = self.debug

    def format_file_list_line(self, line):
        """A formatter run on each line of the file list. Shortens each file path down to its base name.

        :param line: The unformatted line.
        :type line: str

        :return: A formatted line.
        :rtype str
        """

        return os.path.basename(line)

    def update_file_list(self):
        """Update the file list based on the selected folder."""

        # Simply calling self.file_list.set_values() to refresh the list while files are already present causes
        # weird selection issues. I think this may be an issue with the npyscreen module. Manually clear selection to
        # account for this.

        # Clear the list of file's "value" rather than "values" to reset the selection checkboxes.
        self.file_list.value = None

        # Now that the track selection has been cleared, clear the fields as well.
        for field in self.fields:
            field.clear()

        # Clear our own list of selected tracks to stay in sync.
        self.selected_mp3_tracks.clear()

        if self.folder_input.get_value() is not None:
            mp3_files = get_mp3_files(self.folder_input.get_value())

            # Use the filenames are values rather than MP3Tracks. If the folder has a large number of MP3 files and the
            # user does not want to edit them all, creating MP3Tracks for each file could be needlessly expensive.
            self.file_list.set_values(mp3_files)
            self.file_list.update()

            if len(mp3_files) == 0:
                npyscreen.notify_confirm("No MP3 files found in selected folder.", "Error")
                self.set_list_and_editor_visibility(False)
                return
            else:
                self.set_list_and_editor_visibility(True)

    def set_list_and_editor_visibility(self, is_visible):
        """Set the visibility of the file list and tag editor fields.

        :param is_visible: True to set the list and editor fields visible, false to hide them.
        :type is_visible: bool
        """

        hidden = not is_visible

        self.file_list.hidden = hidden
        self.select_all_files_button.hidden = hidden
        self.save_button.hidden = hidden
        self.rename_button.hidden = hidden
        self.album_art_search_box.hidden = hidden
        self.search_button.hidden = hidden
        for field in self.fields:
            field.set_visibility(is_visible)

    def select_all_files(self):
        """Select all files in the file list."""

        self.file_list.value = []
        for i in range(len(self.file_list.entry_widget.values)):
            self.file_list.value.append(i)

        # Manually setting the values does not trigger the listener so call it directly.
        self.on_file_list_selection_change()

    def save_entries_to_tracks(self):
        """Apply selected editor field values to selected tracks and save each file."""

        for track in self.selected_mp3_tracks:
            for field in self.fields:
                if field.is_selected():
                    field.apply_value_to_track(track)

            track.save_tag()

    def rename_files(self):
        """Rename the selected files based on their saved tag information.

        The files are saved in the form: "<artist> - <album> - <title>.mp3"
        """

        selected_file_paths = self.file_list.get_selected_objects()

        if selected_file_paths is None:
            npyscreen.notify_confirm("No files selected to rename.", "Error")
        else:
            files_not_enough_info = []
            files_already_exist = []

            for file_path in selected_file_paths:
                track = self.mp3_tracks[file_path]
                artist = track.get_artist()
                album = track.get_album()
                title = track.get_title()

                file_name_info = []
                if artist is not None:
                    file_name_info.append(artist)
                if album is not None:
                    file_name_info.append(album)
                if title is not None:
                    file_name_info.append(title)

                new_base_filename = ""

                if len(file_name_info) > 0:
                    new_base_filename = ' - '.join(file_name_info) + ".mp3"
                else:
                    # If there isn't enough metadata to create a filename, keep track of the file for an error later.
                    files_not_enough_info.append(file_path)
                    continue

                # Don't bother trying to rename if the file name is already the same.
                if os.path.basename(track.get_file_path()) == new_base_filename:
                    continue

                try:
                    track.rename_file(new_base_filename)
                except FileExistsError:
                    # If a file with the same name already exists, keep track of the file for an error later.
                    files_already_exist.append(file_path)
                    continue

                # The filename has changed, so the keys in the filename => MP3Track map must be updated.
                del self.mp3_tracks[file_path]
                # To be consistent, make sure to key on the entire path, not just the new base filename.
                self.mp3_tracks[track.get_file_path()] = track

            # Construct and show an error message if necessary.
            error_string = ""
            if len(files_not_enough_info) > 0:
                error_string += "Unable to rename the following file(s) due to insufficient metadata:\n- "
                error_string += '\n- '.join(files_not_enough_info)
            if len(files_already_exist) > 0:
                error_string += "Unable to rename the following file(s) because file with same name already exists:\n- "
                error_string += '\n- '.join(files_already_exist)
            if len(error_string) > 0:
                npyscreen.notify_confirm(error_string, "Error", wide=True)

            # Refresh the file list to reflect the new file names.
            self.update_file_list()

    def on_file_list_selection_change(self):
        """Lazily create MP3Tracks as the file selection changes."""

        # Clear old set of selected tracks.
        self.selected_mp3_tracks.clear()

        # Get a list of the selected files from the list widget.
        selected_file_paths = self.file_list.get_selected_objects()

        if selected_file_paths is None:
            # If no files are selected, clear all of the fields.
            for field in self.fields:
                field.clear()
        else:
            # For each selected file, create an MP3Track wrapper if one has not already been created.
            for file_path in selected_file_paths:
                if file_path not in self.mp3_tracks:
                    self.mp3_tracks[file_path] = MP3Track(file_path)

                self.selected_mp3_tracks.add(self.mp3_tracks.get(file_path))

        for field in self.fields:
            field.update_value_from_tracks(self.selected_mp3_tracks)

    def lookup_album_art(self):
        # TODO: Document this once I figure out what this method is going to do exactly.

        album_art_urls = album_art_utils.fetch_album_art(self.album_art_search_box.get_value())

        # For now, just launch the five first hits.
        for i in range(5):
            if i < len(album_art_urls):
                webbrowser.open_new_tab(album_art_urls[i])
            else:
                break

        # TODO: Eventually apply a chosen URL all of the selected tracks.
        # try:
        #     track.clear_pictures()
        #     track.add_picture_from_url(chosen_album_art_url)
        #     track.save_tag()
        # except (ValueError, URLError) as error:
        #             print("Error: Unable to add album art. " + error.message)
        # else:
        #     print("Error: Unable to find album art.")

    def adjust_widgets(self):
        """This method can be overloaded by derived classes. It is called when editing any widget, as opposed to the
        while_editing() method, which may only be called when moving between widgets. Since it is called for every
        keypress, and perhaps more, be careful when selecting what should be done here.
        """

    def while_editing(self, *args, **keywords):
        """This function gets called during the edit loop, on each iteration of the loop. It does nothing: it is here to
        make customising the loop as easy as overriding this function. A proxy to the currently selected widget is
        passed to the function.
        """

    def debug(self):
        """Fired when the debug button is pressed."""
        file = open("debug", "w+")
        file.write(("\n".join(list(self.mp3_tracks.keys()))))
        file.close()


class Application(npyscreen.NPSAppManaged):
    """The overall application class."""

    def onStart(self):
        """Perform application initialization."""
        self.addForm("MAIN", TrackEditorForm, name="MP3 Tagger")


if __name__ == "__main__":
    try:
        application = Application().run()
    except npyscreen.wgwidget.NotEnoughSpaceForWidget:
        print()
        print("ERROR: Not enough space to display UI.")
        print("       Please maximize your terminal window, increase your resolution if necessary, and restart.")
        print()
        exit(1)
