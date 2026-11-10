# WhatASmallKawaiiThings

Windows 바탕화면에서 생활하는 치이카와 랏코 데스크톱 펫입니다.

## STEP 1

투명한 최상위 창에 캐릭터 PNG를 표시하고, 실제 픽셀만 드래그할 수 있습니다. 종료하면 마지막 위치가 `data/state.json`에 저장됩니다.

랏코 PNG는 아직 없습니다. `assets/images/rakko.png`는 표시와 드래그 테스트를 위한 임시 이미지입니다. 나중에 같은 경로의 파일만 교체하면 됩니다.

## 실행

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

종료는 캐릭터 위에서 마우스 오른쪽 버튼입니다. 종료할 때만 위치가 저장됩니다.

## 테스트

이 저장 환경에는 Windows 바탕화면과 PySide6를 실행할 수 없습니다. 위치 제한, PNG 투명도, JSON 저장 형식만 확인했습니다.

```powershell
python -m unittest tests.test_step1 -v
```

Windows에서 아래를 직접 확인해 주세요.

- 바탕화면과 다른 창 위에 베이지색 타원형 임시 캐릭터가 보이는지
- 불투명 픽셀만 드래그되고, 투명 영역 클릭은 뒤 프로그램으로 통과하는지
- 화면 가장자리 밖으로 벗어나지 않는지
- 오른쪽 버튼으로 종료한 뒤 재실행하면 같은 위치에 나오는지
