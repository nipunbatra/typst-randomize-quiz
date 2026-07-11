EXAM ?= exams/quiz2.typ
SET ?= A

ifeq ($(shell uname),Darwin)
TYPST_LOCAL := $(HOME)/Library/Application Support/typst/packages/local
else
TYPST_LOCAL := $(HOME)/.local/share/typst/packages/local
endif
PKG_VERSION := $(shell sed -n 's/^version = "\(.*\)"/\1/p' quizforge/typst.toml)

.PHONY: build test watch watch-key install-local uninstall-local clean

build:
	python3 scripts/build.py $(EXAM)

test:
	python3 -m pytest tests -q

watch:
	mkdir -p build && typst watch $(EXAM) build/preview.pdf --root . --input set=$(SET) --input mode=exam

watch-key:
	mkdir -p build && typst watch $(EXAM) build/preview-key.pdf --root . --input set=$(SET) --input mode=key

# Symlink the package as @local/quizforge:<version> so any project on this
# machine can `#import "@local/quizforge:$(PKG_VERSION)": *`
install-local:
	mkdir -p "$(TYPST_LOCAL)/quizforge"
	ln -sfn "$(CURDIR)/quizforge" "$(TYPST_LOCAL)/quizforge/$(PKG_VERSION)"
	@echo "installed: @local/quizforge:$(PKG_VERSION)"

uninstall-local:
	rm -f "$(TYPST_LOCAL)/quizforge/$(PKG_VERSION)"

clean:
	rm -rf build
