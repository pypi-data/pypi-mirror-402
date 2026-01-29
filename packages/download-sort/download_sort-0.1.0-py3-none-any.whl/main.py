import random
import shutil
import time

from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, DirCreatedEvent, FileCreatedEvent

if __name__ == "__main__":
    downloads_folder = Path("~/Downloads").expanduser()
    target_folder_name = "should-be-deleted"

    class MyHandler(FileSystemEventHandler):
        def on_created(self, event: DirCreatedEvent | FileCreatedEvent) -> None:
            print("New file created: ", event.src_path)

            time.sleep(0.5)

            # macos .app files are actually directories (bundles), so recursive monitoring
            # is required to detect their creation. However, this triggers events for every
            # single file inside the bundle.
            # I filter these out by ensuring the event comes directly from the root
            # of the Downloads folder, ignoring nested paths.
            path_segments = event.src_path.split("/")
            if path_segments[-2] != downloads_folder.name:
                print("Folder skipped: ", event.src_path)
                return

            should_be_deleted: list[Path] = []

            for file in downloads_folder.glob("*"):
                if file.suffix in (".app", ".dmg"):
                    should_be_deleted.append(file)

            should_be_deleted_folder = Path(f"{downloads_folder}/{target_folder_name}")
            should_be_deleted_folder.mkdir(exist_ok=True)

            for file in should_be_deleted:
                target = str(should_be_deleted_folder) + "/" + file.name

                if Path(target).exists():
                    random_num = random.randint(1, 1000)
                    target = f"{should_be_deleted_folder}/{file.stem} {random_num}{file.suffix}"

                if file.exists():
                    shutil.move(str(file), target)

                print("Target position: " + target)

            print(f"{len(should_be_deleted)} files should be deleted")


    observer = Observer()
    observer.schedule(MyHandler(), downloads_folder, recursive=True)
    observer.start()
    try:
        while observer.is_alive():
            observer.join(1)
    finally:
        observer.stop()
        observer.join()