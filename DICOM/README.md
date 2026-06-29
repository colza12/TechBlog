# DICOMとは何か、なぜ危険なのか：PACSとDICOMサーバ攻撃から考える医療サイバーセキュリティ
## 前提

本稿は、医療機関・医療機器ベンダ・PACS運用者・セキュリティ担当者が、医療サイバーセキュリティ上のリスクを理解し、医療機関レッドチーム演習や医療機器の脆弱性診断を安全に設計するための技術解説である。

本稿の再現コードは、ローカルの検証環境・合成患者データ・許可済みのラボ環境を前提にする。実在の医療機関、PACS、医療機器、検査装置、クラウドPACS等に対して無断で実行しないでください。  
実病院ネットワーク、医療機器、PACS、本番DICOMサーバに対して実行する場合は、少なくとも以下の条件を満たす必要がある。
* 医療機関・運用ベンダ・機器ベンダの明示的な許可
* 試験対象、時間帯、停止条件、連絡経路を定義したルール・オブ・エンゲージメント
* 合成患者データまたは検証用データのみの使用
* 本番診療影響を即時停止できる監視体制
* C-STORE負荷、C-FIND件数、ストレージ使用量の上限設定

## 1. DICOM概要
DICOM(Digital Imaging and Communications in Medicine)は、医用画像と関連情報を扱うための標準規格である。  
CT、MRI、X線、超音波、内視鏡、放射線治療計画装置、PACS、読影端末、RIS、HIS、電子カルテ連携などで使われる。

DICOMは、大きく分けて以下の2つを含む。
| 領域 | 内容 |
| - | - |
| ファイル形式 | 医用画像、患者情報、検査情報、装置情報、UID、メタデータを含むファイル形式 |
| ネットワーク通信 | PACSやモダリティ間での画像送信、検索、取得、保存を行うプロトコル |

DICOM通信では、通信主体をApplication Entity(AE)と呼ぶ。各AEは`AE Title`という識別子を持つ。
| 機器 | AE Title例 |
| - | - |
| CT装置 | `CT01` |
| MRI装置 | `MRI01` |
| PACS | `PACS01` |
| 読影端末 | `VIEWER01` |

## 2. PACS概要
PACS(Picture Archiving and Communication System)は、医用画像の保存・検索・配信を担う中核システムである。

典型的な構成は以下の通り。
```
[CT / MRI / X-ray]
        |
        | DICOM C-STORE
        v
      [PACS]
        ^
        | DICOM C-FIND / C-MOVE / C-GET
        |
[読影端末 / 画像ビューア / RIS連携]
        |
        v
[放射線科医 / 臨床医]
```

PACSは医療機関の画像診断ワークフローの中心に位置し、臨床データプレーンである。  
PACSやDICOM通信に障害が発生したときの影響は以下の通り。
* CT画像が読影医に届かない
* 救急患者の画像確認が遅れる
* 手術前画像が参照できない
* 過去画像との比較ができない
* 放射線科・救急・外科・内科の連携が止まる
* 診断や治療判断が遅れる

攻撃者にとっての価値は以下の通り。
* 患者情報を含むメタデータが集約されている
* 画像データが大量に保存されている
* 検査日、検査種別、診療科、紹介医、施設名などが分かる
* 可用性低下が診療遅延に直結する
* 医療機器・読影端末・部門システムとの信頼関係がある

## 3. DICOM通信の基本と主要操作
DICOM通信では、クライアント側がPACSにAssociationを張り、対応するDICOMサービスを実行する。  
代表的なサービスは以下の通り。
| サービス | 用途 | 攻撃面 |
| - | - | - |
| C-ECHO | 疎通確認 | 存在確認、AE応答確認 |
| C-STORE | 画像送信/保存| 不正画像投入、ストレージ圧迫 |
| C-FIND | 検索 | メタデータ列挙、患者情報漏えい |
| C-MOVE | 画像転送要求 | 不正転送、内部構成把握 |
| C-GET | 画像取得 | 画像情報の取得 |

### C-ECHO
疎通確認。いわゆるDICOM pingのようなもの。

攻撃者視点では、C-ECHOが通るだけで以下について分かる。
* DICOMサーバが存在する
* AE Titleが正しい可能性がある
* Associationが確立できる
* ファイアウォールやACLで遮断されていない

### C-STORE
画像やDICOMオブジェクトをPACSへ送信したり、保存させるためのサービス。  
通常の医療ワークフローでは、CTやMRIなどのモダリティがPACSへ検査画像を送信する。

攻撃者視点では、DICOMサーバに対してC-STOREは以下の操作を成立させ得る。
* 不正なDICOMオブジェクトの投入
* 偽患者・偽検査データの登録
* ストレージ圧迫
* バックアップ容量の圧迫
* 画像ビューアやPACSパーサへの遅延型攻撃
* インデックス、サムネイル生成、画像変換処理への負荷

### C-FIND
PACS内の患者、検査、シリーズ、画像インスタンスを検索するためのサービス。
攻撃者視点では、C-FINDが適切に制御されていない場合、PACS内のメタデータが広範囲に列挙することができ、画像本体を取得しなくても、メタデータだけで多くの個人情報・診療情報が漏洩する。

C-FINDで露出し得る代表的な属性は以下の通り。
| DICOM Tag | Keyword | 内容 |
|---|---|---|
| `(0010,0010)` | `PatientName` | 患者氏名 |
| `(0010,0020)` | `PatientID` | 患者ID |
| `(0010,0030)` | `PatientBirthDate` | 生年月日 |
| `(0010,0040)` | `PatientSex` | 性別 |
| `(0008,0050)` | `AccessionNumber` | オーダ・検査識別子 |
| `(0008,0020)` | `StudyDate` | 検査日 |
| `(0008,0060)` | `Modality` | CT、MR、USなど |
| `(0008,0080)` | `InstitutionName` | 医療機関名 |
| `(0008,0090)` | `ReferringPhysicianName` | 依頼医 |
| `(0008,1030)` | `StudyDescription` | 検査内容 |
| `(0008,103E)` | `SeriesDescription` | シリーズ内容 |
| `(0018,1030)` | `ProtocolName` | 撮像プロトコル |
| `(0018,1000)` | `DeviceSerialNumber` | 装置シリアル |
| `(0008,1010)` | `StationName` | 装置名 |
| `(0020,000D)` | `StudyInstanceUID` | 検査UID |
| `(0020,000E)` | `SeriesInstanceUID` | シリーズUID |
| `(0008,0018)` | `SOPInstanceUID` | 画像インスタンスUID |

## 4. DICOMのリスク
### 平文通信の危険性
DICOMは、院内の閉域ネットワークで使われる前提が強かった。そのため、現場ではDICOM通信が平文のまま運用されていることがある。  
攻撃者が院内ネットワークの一部を観測できる場合、DICOM通信の盗聴により、患者情報や臨床ワークフローが露出する可能性がある。  
特に問題なのは、DICOMが「医療機器同士の通信だから安全」という前提で、TLSや認証なしに許可されているケースである。  
HTTP管理画面には認証があっても、DICOMポート側には認証がない、またはAE Titleベースの緩い制御しかない、という構成も珍しくない。

平文DICOMは、以下のようなリスクを持つ。
| リスク | 内容 |
| - | - |
| Confidentiality | 患者情報・画像の漏えい |
| Integrity | 改ざん検知が困難 |
| Availability | 不正通信を識別しにくい |
| Accountability | 誰が送信したかを厳密に追跡しにくい |

### Metadata leakage
DICOMの危険性は画像本体だけでなく、むしろ初期侵害後の攻撃者にとっては、C-FINDによるメタデータ列挙の方が低ノイズで有用な場合がある。

メタデータ例：
```
PatientName: YAMADA^TARO
PatientID: 12345678
PatientBirthDate: 19700101
PatientSex: M
StudyDate: 20260619
StudyDescription: Head CT
InstitutionName: Example Hospital
Manufacturer: ExampleVendor
ManufacturerModelName: CT-Example-9000
StationName: CTROOM01
ReferringPhysicianName: SUZUKI^HANAKO
```

メタデータから分かることの例:
* どの患者がいつ検査を受けたか
* がん、脳卒中、外傷、妊娠、感染症などを推測できる検査名
* 病院内の装置構成
* 部門や診療科の運用パターン
* 高価な医療機器の存在
* 検査件数、繁忙時間帯
* 患者ID体系
* 他システムとの連携キー

以上の情報は、攻撃者にとって以下の価値を持つ。
* 患者情報の取得
* 医療機関名の特定
* 装置ベンダ・機種の特定
* 部門構成の推測
* 検査種別の把握
* 高リスク患者・救急患者・特定診療科の推測
* 標的型攻撃の材料

これは、単なるプライバシー問題に留まらない。攻撃者が医療機関の業務構造を理解し、後続の恐喝、業務妨害、標的型攻撃に使える情報になる。  
特に装置名、メーカー名、ソフトウェアバージョン、Station Name等は、医療機器の脆弱性診断において重要な資産情報になる。

### 匿名化不備
DICOMの匿名化は困難である。  
`PatientName`や`PatientID`を消しただけでは不十分である。DICOMには多数のタグがあり、Private Tagや自由記述欄に個人情報が残ることがある。

匿名化不備が起きやすい箇所は以下の通り。
| 領域 | 問題 |
| - | - |
| Patient系タグ | 氏名、ID、生年月日、性別 |
| Study系タグ | 検査日、検査説明、依頼医 |
| Institution系タグ | 病院名、部門名 |
| Physician系タグ | 医師名、紹介医名 |
| Device系タグ | 装置名、Station Name |
| Private Tag | ベンダ独自情報 |
| Pixel Data | 画像内焼き込み文字 |
| Structured Report | レポート本文 |
| PDF Encapsulation | 添付文書内の個人情報 |
| UID | 再識別可能性 |

特にPrivate Tagはベンダ固有情報を含むことがあり、一般的な匿名化処理から漏れやすい。  
匿名化を行う場合は、DICOMのBasic Application Confidentiality Profile等の考え方に沿い、タグ削除、UID再生成、日付シフト、Private Tag処理、Burned-in Annotation確認、Pixel Data検査まで含める必要がある。

### AE Title spoofing
AE TitleはDICOM通信上の識別子であり、最大16文字の文字列である。  
ただし、単なるIDであって、単独では認証情報ではないことに注意が必要である。

悪い例：
```
Allowed AE Title: CT_ROOM_01
Allowed IP: 192.168.10.20
```
この設計では、攻撃者が同一ネットワーク内で送信元IPやAE Titleの制御が可能な状況にある場合、`CT_ROOM_01`と名乗るだけでPACSがAssociationを受け入れる可能性がある。

さらに悪いケースでは、AE Titleから以下の情報を容易に推測できる。
* 装置ラベル
* 設定資料
* 過去のDICOMファイル
* DICOM通信の平文キャプチャ
* PACSログ
* `StationName`
* モダリティ命名規則

対策としては、以下を組み合わせて対応づける必要がある。
* AE Title
* 送信元IP制限
* ネットワークセグメント
* DICOM TLS
* クライアント証明書
* 装置台帳
* PACS側の詳細ログ
* 不審なAssociationの検知

### storage abuse
C-STOREが広く許可されている場合、DICOMサーバはストレージ悪用の対象になる。

攻撃パターンは以下のようなものが考えられる。
* 大量のDICOMオブジェクト投入
* 巨大Pixel Data投入
* 重複SOP Instanceの大量投入
* 偽Study/Seriesの作成
* 圧縮画像の展開時に容量が膨らむデータ投入
* バックアップ対象データの水増し
* インデックスDB肥大化
* サムネイル生成や画像変換ジョブの滞留

医療現場では、ストレージ枯渇は以下のような直接的な影響が発生する。
* 新規検査画像をPACSへ送れない
* モダリティ側の送信キューが詰まる
* 読影が遅れる
* 過去画像参照が遅くなる
* 救急・手術・外来の判断が遅れる
* 再撮影や手作業搬送が発生する

### Malicious DICOM
Malicious DICOMとは、DICOMファイル自体を攻撃媒体として使う考え方である。  
仕様上はDICOMとして解釈できるが、受信側の実装にとって危険な構造を持つこともある。

| 分類 | 概要・例 | 具体的なデータの手口 / 狙われる処理 |
| - | - | - |
| Preamble悪用 | 先頭128バイトの自由領域の悪用 | ・ポリグロット攻撃(.exeなどのマルウェア実行コードを埋め込み、画像と見せかけてウイルスを実行させる) |
| 異常なメタデータ | 極端に長い文字列、不正文字、改行、制御文字 | ・巨大な文字列属性によるバッファオーバーフロー<br>・異常に深いSequence(入れ子構造)によるスタックオーバーフロー |
| 不正なVR / Value Length | 規格外の長さ、矛盾した型 | ・壊れたLength（領域確保の計算バグを誘発） |
| 異常なPixel Data | 巨大画像、破損圧縮データ | ・圧縮画像の展開爆弾(メモリ枯渇によるフリーズ) |
| Transfer Syntax悪用 | 実装依存のデコーダを狙う | ・想定外のTransfer Syntax(特定の脆弱なライブラリを強制呼び出し)<br>・JPEG/JPEG2000/RLEなど画像コーデック実装の脆弱性を狙うデータ |
| Private Tag濫用 | ベンダ固有処理のバグを誘発 | ・多数のPrivate Tag(独自実装のパースエラーを狙う) |
| Encapsulated PDF | PDFビューア側の攻撃面 | ・埋め込みPDFを開く際の脆弱性悪用 |
| Structured Report | テキスト処理・HTML変換時の注入 | ・HTML変換時のスクリプト注入(インジェクション攻撃)<br>・Viewerが表示時に処理する説明文、オーバーレイ、Presentation State |
| DICOMDIR | メディア取り込み処理への攻撃 | ・CD-RやUSBなどのメディアからの一括取り込み処理への攻撃 |
| AI・診断機能への攻撃 | 判定アルゴリズムのバグや誤認を狙う | ・敵対的攻撃(Adversarial Attack：画像に微細なノイズを仕込み、AI診断に誤診を起こさせる) |
| 通信プロトコル悪用 | ネットワーク機能(C-STORE等)の脆弱性 | ・不正なDICOMコマンドによるPACSサーバーの遠隔強制終了(DoS)やRCE |
| システム連携・機能特有 | 各種変換・出力処理の隙を狙う | ・サムネイル生成処理を狙うデータ<br>・Export処理や変換処理を狙うデータ |

DICOMは複雑なフォーマットであり、以下のような複数のコンポーネントを通過し、多数の後段処理がDICOMを再パースする。
```
DICOM receiver
  -> metadata parser
  -> database indexer
  -> image decoder
  -> thumbnail generator
  -> web viewer
  -> report system
  -> AI analysis pipeline
  -> export converter
  -> archive / backup
```
C-STOREで投入されたDICOMは、後から別のコンポーネントで処理される保存型攻撃面になり得る。加えて、parser attackの攻撃面を広げる。

### Parser attack
