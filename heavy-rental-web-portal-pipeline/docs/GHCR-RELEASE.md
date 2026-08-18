# Portal Release: GHCR login and push

**App repo:** [Heavy-Rental/heavy-rental-react-web-portal](https://github.com/Heavy-Rental/heavy-rental-react-web-portal)  
**Workflow:** `release-pipeline.yml` Packaging job (runs from `portal-release-caller.yml`)

Academy CD (`web-portal-cd-academy.yml`) does **not** log into GHCR. Guests pull a **public** tag with no token. This file is only about Release Packaging.

Install checklist: [`PREPARE-PORTAL-REPO.md`](PREPARE-PORTAL-REPO.md). Everyday CD: [`BOOTSTRAP.md`](BOOTSTRAP.md).

---

## Do not set `GITHUB_TOKEN`

GitHub Actions injects `secrets.GITHUB_TOKEN` on every run. Do **not** create a repository or Environment secret with that name. Do **not** put a PAT in `GITHUB_TOKEN`.

Release logs in with:

```yaml
username: ${{ github.actor }}
password: ${{ secrets.GITHUB_TOKEN }}
```

The caller already has `permissions: packages: write`. That is enough for the token.

Org check (once): Heavy-Rental → Settings → Actions → General → Workflow permissions → allow GITHUB_TOKEN to create and write packages.

---

## Why “Login to GitHub Container Registry” is skipped

Those steps are gated:

```text
if: github.event_name != 'pull_request'
```

| How the run started | Login | `docker push` | Image tar artifact |
| --- | --- | --- | --- |
| PR `develop` → `master` | Skipped | Skipped | Yes |
| **Published GitHub Release** | Runs | Runs | Yes |

A develop→master PR is still a `pull_request` event. Skipped login on that run is expected. The tar is still uploaded.

---

## How to get a GHCR image

1. Merge to `master` in `heavy-rental-react-web-portal`.
2. In that repo: **Releases → Draft a new release → Publish release**  
   (or `gh release create v1.0.0 --generate-notes` from `master`).
3. Wait for workflow **Release** → job **Packaging**.
4. Confirm **Login to GitHub Container Registry** and **Push Docker image to GHCR** ran (not skipped).
5. Image names (owner lowercased):

   ```text
   ghcr.io/heavy-rental/heavy_rental_web_portal:<x.y.z>
   ghcr.io/heavy-rental/heavy_rental_web_portal:latest
   ```

   `<x.y.z>` is the previous GHCR semver with the patch bumped. First publish is `1.0.0`. An existing version tag is not overwritten.

6. Org **Packages** → `heavy_rental_web_portal` → **Package settings** → visibility **Public**.  
   Private GHCR fails Academy CD on purpose (no PAT on the guest).

7. Set Environment **`academy`** variable `PORTAL_IMAGE` to the **new** version tag, for example:

   ```text
   ghcr.io/heavy-rental/heavy_rental_web_portal:1.0.0
   ```

   Prefer a new version tag each deploy (`compose up` is not `--pull always`). `:latest` works only if guests already pull it after you pushed.

---

## Optional: deploy the PR tar (no GHCR)

If you only have a develop→master PR:

1. Download artifact `web-portal-release-docker-image`.
2. Upload the `.tar.gz` somewhere the lab can read (`s3://` or HTTPS).
3. Set `IMAGE_HTTP_URL` / `image_http_url` **and** a compose tag that matches the loaded image name (`PORTAL_IMAGE` or `image_ref`).

The tar includes the GHCR tag names, so after `docker load` you can still use `ghcr.io/heavy-rental/heavy_rental_web_portal:<tag>` locally on the guest.

---

## Do not

- Expect GHCR from a `develop` → `master` PR alone
- Add a `GITHUB_TOKEN` secret
- Put a PAT on the guest or in Academy Secrets Manager
- Point `PORTAL_IMAGE` at a private GHCR tag
- Run Release from this pipeline-development repo and expect `ghcr.io/heavy-rental/…` (push uses the **calling** repo owner)
