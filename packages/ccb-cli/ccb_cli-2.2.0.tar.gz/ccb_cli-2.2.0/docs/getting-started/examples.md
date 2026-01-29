# 使用示例

一位 Linux 用户的 Home 目录下具有以下内容：
```
.
├── comic_books
│   ├── comic_book1.zip
│   ├── comic_book2
│   └── comic_book3
│       ├── chapter1.7z
│       ├── chapter2.cbt
│       └── chapter3
└── my_favorites
    └── awesome one.cbr
```
## 示例 1: 转换 comic_book1.zip 文件为 cbz

```bash
ccb ~/comic_books/comic_book1.zip
# 输出：~/comic_books/comic_book1.cbz
```

## 示例 2: 转换 comic_book2 文件夹为 cbz

```bash
ccb ~/comic_books/comic_book2
# 输出：~/comic_books/comic_book2.cbz
```

## 示例 3: 批量转换 comic_book3 的章节到 cbt

```bash
cd ~/comic_books/comic_book3
ccb -t cbt chapter1.7z chapter2.cbt chapter3
# 输出：chapter1.cbt, chapter3.cbt
# 注意到 chapter2.cbt 不发生转换
```

## 示例 4: 处理带有空格的路径

```bash
# 使用引号包裹带有空格的路径
ccb "~/my_favorites/awesome one.cbr"
# 输出：~/my_favorites/awesome one.cbz
```

## 示例 5：批量转换 Home 下的所有源后删除，静默输出

```bash
ccb -c ~ -R -q
```
命令完成后，将产生如下结构：
```
.
├── comic_books
│   ├── comic_book1.cbz
│   ├── comic_book2.cbz
│   └── comic_book3
│       ├── chapter1.cbz
│       ├── chapter2.cbz
│       └── chapter3.cbz
└── my_favorites
    └── awesome one.cbz
```
