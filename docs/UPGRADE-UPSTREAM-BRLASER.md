# Upgrade an existing PrintBridge app to upstream brlaser (TrueNAS 25.10)

This is a test build. The existing image contains Debian's brlaser 6.2.7;
the new image builds upstream pdewacht/brlaser v6 from commit
`23117fe9e0266396e4791cdae84d979928aed135`. An already reported
`USB disconnect` during printing may persist: the driver creates printer data,
but CUPS's USB backend sends it to the printer.

## 1. Copy the new source into your existing GitHub Desktop folder

1. Download the updated PrintBridge ZIP and choose **Extract All** in Windows.
2. In GitHub Desktop select your existing `printbridge` repository. Choose
   **Repository → Show in Explorer** to open its real folder (containing
   `Dockerfile`). Do not create a second repository.
3. In a second File Explorer window, open the **newly extracted** `printbridge`
   folder, the one containing `Dockerfile`.
4. Copy the new `Dockerfile`, `README.md` and `docs` folder into the existing
   repository folder. When Windows asks, choose **Replace the files in the
   destination**. Leave `custom-app.yaml.template` and your TrueNAS YAML as
   they are. Check GitHub Desktop **Changes** shows at least `Dockerfile`.
5. Enter `Build upstream brlaser v6` under **Summary**, click **Commit to
   main**, then **Push origin**. Open your repository on GitHub and verify
   `Dockerfile` contains `23117fe9e0266396e4791cdae84d979928aed135`.

## 2. Build and publish a separate image version

1. In your GitHub repository, open **Releases → Draft a new release**.
2. Under **Choose a tag**, type `v0.1.1` and choose **Create new tag:
   v0.1.1** on the latest `main` branch. Do not reuse `v0.1.0`.
3. Set title to `v0.1.1 upstream brlaser test`, mark it as a **pre-release**,
   and click **Publish release**.
4. Open **Actions → Build released image** and wait for a green run **for tag
   v0.1.1**. The workflow builds brlaser in GitHub Actions; you do not run
   compilers on TrueNAS. If it is red, open the failed step and keep using
   `v0.1.0`. Do not change the TrueNAS image tag yet.
5. On your GitHub profile, open **Packages → printbridge**. Check that
   `v0.1.1` exists and that package visibility is **Public**.

## 3. Upgrade the existing app without deleting its queues

1. Note your existing queue name; for example `Brother_HL-2030`. If older
   failed jobs are pending, remove only those jobs in the CUPS Jobs page
   before testing so they do not print unexpectedly during the upgrade.
2. TrueNAS **Apps → Installed → printbridge → Edit**. In the existing YAML,
   change **only** the `image:` tag from `:v0.1.0` to `:v0.1.1`. Keep the
   `config:` and `spool:` volumes and all other fields unchanged. Save and
   wait until the app is Running again. Never delete the app to upgrade it.
3. In TrueNAS **System → Shell**, run:

   ```sh
   sudo docker exec ix-printbridge-printbridge-1 lpinfo -m | grep -i 'HL-2030 series'
   ```

   Confirm the list contains `brlaser`, then check the existing queue:

   ```sh
   sudo docker exec ix-printbridge-printbridge-1 lpstat -v
   ```

4. With Brother visible in `lsusb`, print **one** test page from PrintBridge.
   Verify paper physically exits. If USB disconnects again, copy the fresh
   `sudo dmesg -T | tail -n 50` and CUPS error lines; changing the brlaser
   version did not solve the USB-level failure.

## Roll back

In **Apps → Installed → printbridge → Edit**, change only the image tag back to
`:v0.1.0`, save, and wait for Running. The same named volumes keep existing
queues and pending jobs when the container is replaced. Do not delete the app
or remove volumes as part of rollback.
