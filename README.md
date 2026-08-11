# [baldman.github.io](https://baldman.justsquad.su/)

[![Build and deploy GH Pages](https://github.com/ni-gushch/ni-gushch.github.io/actions/workflows/gh_pages.yml/badge.svg)](https://github.com/ni-gushch/ni-gushch.github.io/actions/workflows/gh_pages.yml)
[![pages-build-deployment](https://github.com/ni-gushch/ni-gushch.github.io/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/ni-gushch/ni-gushch.github.io/actions/workflows/pages/pages-build-deployment)

![logo](./img/img_1.png)

Сайт для больших статей, которые не помещаются в формат Telegram.

## На чем строится

Основной движок [Zola](https://github.com/getzola/zola)

Используется тема [Goyo](https://github.com/hahwul/goyo)

Обновление темы

```bash
git submodule update --remote themes/goyo
```

### Удаление сабмодуля

# 1. Unregister the submodule from Git configuration
```bash
git submodule deinit -f path/to/submodule
```
# 2. Remove the submodule directory from working tree and index
```bash
git rm -f path/to/submodule
```

# 3. Delete Git's internal cached directory for the submodule
```bash
rm -rf .git/modules/path/to/submodule
```

# 4. Commit the changes to finalize the removal
```bash
git commit -m "Remove submodule at path/to/submodule"
```
