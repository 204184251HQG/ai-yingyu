# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('yy_topic_model.pkl', '.'),
        ('yy_sentence_model.pkl', '.'),
        ('yy_grade_model.pkl', '.'),
        ('yy_diff_model.pkl', '.'),
        ('yy_ensemble_model.pkl', '.'),
        ('data/wordbank/primary.json', 'data/wordbank'),
        ('data/wordbank/middle.json', 'data/wordbank'),
        ('data/wordbank/high.json', 'data/wordbank'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='词途AI英语单词学习闯关系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='词途AI英语单词学习闯关系统',
)
