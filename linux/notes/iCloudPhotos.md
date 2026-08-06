# Download iCloud Photos on Linux

This computer uses `icloudpd` to copy photos and videos from iCloud Photos. It
is already installed in a Conda environment, so no installation or Python
virtual environment is required.

## Existing Setup

- Conda environment: `icloudpd`
- Installed downloader: `icloudpd` 1.32.2
- Working directory: `/mnt/home/Cloud`
- Download directory: `/mnt/home/Cloud/iCloudPhotos`
- Authentication data: `/mnt/home/Cloud/.pyicloud`

`icloudpd` uses a `year/month/day` folder structure by default, matching the
existing photo collection.

## Download Photos

Activate the Conda environment and move to the Cloud directory:

```bash
conda activate icloudpd
cd /mnt/home/Cloud
```

Run the downloader, replacing the example address with the Apple Account email
address:

```bash
icloudpd \
  --directory /mnt/home/Cloud/iCloudPhotos \
  --cookie-directory /mnt/home/Cloud/.pyicloud \
  --size original \
  --set-exif-datetime \
  --username "name@example.com"
```

It is safe to stop the command and run it again later. Existing downloads are
recognised and do not need to be downloaded again.

## Run Without Activating Conda

The same download can be launched from any directory with `conda run`:

```bash
conda run -n icloudpd icloudpd \
  --directory /mnt/home/Cloud/iCloudPhotos \
  --cookie-directory /mnt/home/Cloud/.pyicloud \
  --size original \
  --set-exif-datetime \
  --username "name@example.com"
```

## Test Before Downloading

Add `--dry-run` to see what the downloader would do without downloading media:

```bash
icloudpd \
  --directory /mnt/home/Cloud/iCloudPhotos \
  --cookie-directory /mnt/home/Cloud/.pyicloud \
  --dry-run \
  --username "name@example.com"
```

## Refresh Authentication

If the saved session has expired, refresh it interactively:

```bash
icloudpd \
  --auth-only \
  --cookie-directory /mnt/home/Cloud/.pyicloud \
  --username "name@example.com"
```

Enter the iCloud password and two-factor authentication code when prompted. Do
not put the password directly in the command because it could be saved in shell
history or exposed in the process list.

## Faster Incremental Download

After completing the first full download, add `--until-found 50` to stop after
the downloader finds 50 consecutive previously downloaded items:

```bash
icloudpd \
  --directory /mnt/home/Cloud/iCloudPhotos \
  --cookie-directory /mnt/home/Cloud/.pyicloud \
  --size original \
  --set-exif-datetime \
  --until-found 50 \
  --username "name@example.com"
```

## Update icloudpd

Update `icloudpd` inside its existing Conda environment:

```bash
conda activate icloudpd
python -m pip install --upgrade icloudpd
icloudpd --version
```

If pip reports `Requirement already satisfied`, the latest available version is
already installed. Updating the package does not remove the downloaded photos
or the saved authentication data in `/mnt/home/Cloud/.pyicloud`.

## Important Notes

- The existing `/mnt/home/Cloud/.envrc` refers to a nonexistent Conda
  environment named `pyicloud`. Activate `icloudpd` manually until that file is
  corrected.
- The `icloud` command inside the environment is a Find My iPhone tool. Use
  `icloudpd` to download photos.
- Do not enable options that delete media from iCloud unless deletion is
  intentional and a separate backup has been verified.
- Check available options for the installed version with `icloudpd --help`.
- Keep a second independent backup of important photos.

## Reference

- [iCloud Photos Downloader documentation](https://github.com/icloud-photos-downloader/icloud_photos_downloader)
