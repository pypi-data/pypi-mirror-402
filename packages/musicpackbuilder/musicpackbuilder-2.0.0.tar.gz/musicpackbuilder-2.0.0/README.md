

# MusicPackBuilder — Command Line Usage Guide

MusicPackBuilder converts your audio files into a Minecraft resource pack containing custom music discs. You can run it by double‑clicking the executable or by using command‑line arguments for more control.

This guide explains all available arguments and how to use them.

---

## Basic Usage

If you double‑click the executable, MusicPackBuilder will:

- Open a folder picker so you can choose your audio directory  
- Export processed `.ogg` files into a folder named `Export Files`  
- Build a ready‑to‑use Minecraft resource pack ZIP  

No command‑line knowledge is required.

---

## Command Line Usage

If you prefer using the terminal, you can pass arguments to control how the tool behaves.

```
musicpackbuilder [OPTIONS]
```

---

## `--audio-dir`

Specifies the folder containing your source audio files.

Example:

```
musicpackbuilder --audio-dir "My Songs"
```

If not provided:

- A folder picker will appear  
- If cancelled, the tool defaults to `Audio Files`

---

## `--export-dir`

Specifies where the processed `.ogg` files should be saved.

Example:

```
musicpackbuilder --export-dir "Converted"
```

If not provided, the default is:

```
Export Files
```

---

## `--auto-truncate`

Automatically shortens songs that exceed Minecraft’s disc time limits.

Example:

```
musicpackbuilder --auto-truncate
```

This option removes all prompts related to long songs.

---

## `--skip-long-songs`

Automatically skips songs that exceed the time limit instead of asking.

Example:

```
musicpackbuilder --skip-long-songs
```

---

## Examples

### Fully automatic run

```
musicpackbuilder --audio-dir "My Songs" --auto-truncate
```

### Skip long songs instead of cutting them

```
musicpackbuilder --audio-dir "My Songs" --skip-long-songs
```

### Custom export folder

```
musicpackbuilder --audio-dir "My Songs" --export-dir "OGG Output"
```

### Interactive mode (no arguments)

```
musicpackbuilder
```

---

## Output

After processing, the tool produces:

- A ZIP file containing the complete resource pack  
- No leftover JSON files in the working directory  

The ZIP can be placed directly into your Minecraft `resourcepacks` folder.

