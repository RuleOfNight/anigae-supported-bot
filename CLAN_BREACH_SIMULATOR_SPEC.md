# Đặc Tả Clan Breach Simulator

## 1. Mục tiêu

Xây dựng một web simulator cho tính năng Clan Breach của AniGame. Web cho phép người dùng đăng nhập bằng Discord, tạo túi card cá nhân, chọn team solo/duo, chọn boss hoặc herald, chọn độ khó, sau đó chạy simulator để ước tính sát thương và kết quả trận đấu.

MVP tập trung vào:

- Xác thực tài khoản bằng Discord.
- Đồng bộ card database từ AniGame public database.
- Tạo và quản lý túi card của người dùng.
- Lọc/tìm card theo tên, series, hệ và talent.
- Chọn team solo 3 card hoặc duo 4 card.
- Gộp toàn bộ card của người chơi thành 1 team unit có HP/ATK/DEF/SPD tổng.
- Chọn main boss từ nhóm card clan shop hoặc chọn 1 trong 2 herald cố định.
- Tính stat card/enemy theo rarity, level, evo và ascension.
- Mô phỏng 1 ván đánh giữa player team và đúng 1 enemy.
- Enemy có đánh ngược lại player.
- Tổng SPD quyết định phe đi trước.
- Có RNG crit/dodge, có thể bật/tắt riêng từng phe.
- Có element multiplier cho team nhiều hệ.

Ngoài phạm vi MVP:

- Event timer weekend thật.
- Clan ranking/player ranking.
- Rift Energy.
- Tag Battle confirm flow trên Discord.
- Gambit phase chi tiết.
- Deterioration theo lịch.
- Đồng bộ HP boss/herald live từ game. Simulator chỉ tự tính trận local, không track HP event thật.
- Talent simulator chi tiết. MVP chỉ cần chừa hook để thêm sau.

## 2. Nguồn dữ liệu card

AniGame có web database:

https://www.anigame.gg/database?view=cards

Trang này không công bố API riêng, nhưng hiện đang load card data từ Google Sheets public endpoint.

Cards CSV:

https://docs.google.com/spreadsheets/d/14qAWkLyjMCI6VXgEgtWWDlDq5MQfotHhLYW6p-Qntlc/gviz/tq?tqx=out:csv&sheet=cards

Google Sheets API endpoint đang được frontend sử dụng:

```txt
https://sheets.googleapis.com/v4/spreadsheets/14qAWkLyjMCI6VXgEgtWWDlDq5MQfotHhLYW6p-Qntlc/values/cards!A:ZZ
```

Khuyến nghị: tự build API riêng dạng cache/proxy, không để frontend gọi trực tiếp Google Sheets mỗi lần.

Luồng đồng bộ dữ liệu:

- Backend có job sync định kỳ, ví dụ mỗi 6 giờ hoặc mỗi ngày.
- Fetch CSV/Google Sheets data.
- Normalize vào database của simulator.
- Frontend chỉ gọi API của simulator.
- Nếu Google Sheets endpoint fail, web vẫn dùng cache cũ.

Fields hiện có từ sheet:

```txt
card_name
card_series
card_type
card_hp
card_atk
card_def
card_spd
card_talent
art
last_patch
```

Mapping:

```txt
card_name   -> name
card_series -> series
card_type   -> element
card_hp     -> base_hp
card_atk    -> base_atk
card_def    -> base_def
card_spd    -> base_spd
card_talent -> talent_text
art         -> art_url
last_patch  -> last_patch
```

## 3. Discord Login

Người dùng phải tạo tài khoản bằng Discord OAuth.

Login flow:

1. User bấm "Login with Discord".
2. Redirect sang Discord OAuth.
3. Backend nhận callback và lấy Discord identity.
4. Tạo hoặc update user trong database.
5. Tạo session/JWT cho web.

Discord scope cần thiết:

```txt
identify
```

User data lưu:

```js
{
  discord_id: string,
  username: string,
  global_name: string | null,
  avatar_url: string | null,
  created_at: Date,
  updated_at: Date,
  last_login_at: Date
}
```

## 4. Card Master Model

Card master là card gốc từ database AniGame, chưa áp dụng rarity/level/evo/ascension của user.

```js
{
  id: string,
  source_id: number,
  name: string,
  series: string,
  element: "Fire" | "Water" | "Electric" | "Ground" | "Grass" | "Neutral" | "Light" | "Dark" | "Null" | string,
  base_hp: number,
  base_atk: number,
  base_def: number,
  base_spd: number,
  talent_text: string,
  art_url: string,
  last_patch: boolean,
  source_hash: string,
  source_updated_at: Date,
  created_at: Date,
  updated_at: Date
}
```

Index nên có:

- `name`
- `series`
- `element`
- text index cho `name`, `series`, `talent_text`
- `last_patch`

## 5. User Card Model

User card là bản copy/instance trong túi card của user.

```js
{
  id: string,
  user_id: string,
  card_master_id: string,
  rarity: "SR" | "UR",
  ascend: 0 | 1 | 2 | 3 | 4 | 5,
  evo: 3,
  level: 50 | 60,
  nickname: string | null,
  created_at: Date,
  updated_at: Date
}
```

Rules:

- Evo mặc định và cố định là E3 trong MVP.
- SR max level 50.
- SR max ascension A4.
- UR max level 60.
- UR max ascension A5.
- Khi user chọn rarity:
  - SR -> auto level 50, giới hạn ascend A0-A4.
  - UR -> auto level 60, giới hạn ascend A0-A5.

UI có thể ẩn option evo trong MVP. Nếu sau này cần test E1/E2, thêm Advanced Settings.

## 6. Công thức tính stat card

Stats trong sheet là base stats. Simulator tự tính stat final.

Rarity multiplier:

```txt
SR = 1.8
UR = 2.0
```

Level multiplier:

```txt
level_multiplier = 1 + level * 0.005
```

Evo multiplier:

```txt
evo_multiplier = 1 + 0.15 * (evo - 1)
```

Ascension multiplier:

```txt
asc_multiplier = 1 + ascend * 0.05
```

Final stat:

```txt
final_stat = round(base_stat * level_multiplier * evo_multiplier * asc_multiplier * rarity_multiplier)
```

Áp dụng cho:

```txt
HP
ATK
DEF
SPD
```

Boss level 1400 và herald level 900 dùng chung công thức này. HP của boss/herald cũng lấy từ base HP rồi tính ra final HP bằng công thức stat bình thường.

Ví dụ UR A5 E3 level 60:

```txt
level_multiplier = 1 + 60 * 0.005 = 1.3
evo_multiplier   = 1 + 0.15 * (3 - 1) = 1.3
asc_multiplier   = 1 + 5 * 0.05 = 1.25
rarity_multiplier = 2.0

total_multiplier = 1.3 * 1.3 * 1.25 * 2.0 = 4.225
```

## 7. Card Search và Filter

Dùng chung cho màn hình thêm card vào túi và màn hình chọn card trong simulator.

Filter cần có:

- Search theo card name.
- Filter theo series.
- Filter theo element/hệ.
- Filter theo talent text.
- Filter latest patch only.
- Sort:
  - newest/oldest theo `source_id`
  - name A-Z/Z-A
  - HP high-low
  - ATK high-low
  - DEF high-low
  - SPD high-low

Trong simulator selector:

- Mặc định chỉ hiện card user đã add vào túi.
- Có option "Browse all database" để test card chưa add, nếu muốn.

## 8. Boss và Herald

Mỗi simulation run chỉ đánh 1 enemy:

- Player team vs Main Boss
- Player team vs Herald Of Salvation
- Player team vs Herald Of Damnation

Không mô phỏng boss + 2 herald cùng lúc trong MVP.

### Main Boss

Main boss:

- Random mỗi mùa trong game thật.
- Trong simulator, user có thể tự chọn.
- Main boss được chọn từ card database, nhưng chỉ từ các series thuộc clan shop.
- Main boss là UR A5 level 1400 E3.
- Stats dùng công thức stat bình thường như card.

Series thuộc clan shop:

```txt
Howls Moving Castle
Mashle
Frieren: Beyond Journeys End (Soso no Frieren)
Oshi No Ko
Bucchigiri?!
To Be Hero X
Lycoris Recoil
```

Boss source model đề xuất:

```js
{
  id: string,
  card_master_id: string,
  source: "clan_shop",
  enabled: boolean,
  season_label: string | null,
  created_at: Date,
  updated_at: Date
}
```

### Herald

Herald là 2 card cố định trong database web:

```txt
Herald Of Salvation - ID: 1170
Herald Of Damnation - ID: 1171
```

Rules:

- Herald là UR A5 level 900 E3.
- Stats dùng công thức stat bình thường như card.
- Không cần custom herald table trong MVP nếu 2 card này đã sync được từ public database.
- Nếu sau này database thiếu hoặc ID thay đổi, có thể thêm fallback admin override.

### Difficulty

Enemy stats áp dụng difficulty multiplier:

```txt
Easy       x0.70
Medium     x1.00
Hard       x1.25
Impossible x1.50
```

Difficulty apply vào toàn bộ enemy final stats:

```txt
enemy_hp
enemy_atk
enemy_def
enemy_spd
```

## 9. Simulator Modes

Mode 1: Solo

```txt
Player team = 3 cards
```

Mode 2: Duo

```txt
Player team = 4 cards
```

Team stats:

- Toàn bộ card của người chơi được gộp thành 1 team unit.
- Base HP/ATK/DEF/SPD của team = tổng base stats của các card trong team.
- Final HP/ATK/DEF/SPD của team = tổng final stats của các card trong team.
- Team có 1 thanh HP tổng chung.
- Trong trận không có từng card chết riêng trong MVP.

Duo mode:

- Duo mode đại diện Tag Battle simplified.
- MVP coi 4 card là 1 team chung.
- Tổng damage của duo mode được nhân theo hệ số Tag Battle rồi chia credit đều cho 2 người.

Duo damage/credit:

```txt
objective_damage = raw_team_damage * 2.25
caller_credit = objective_damage / 2
teammate_credit = objective_damage / 2
```

Ghi chú:

- Trong game FAQ có nói mỗi player nhận x1.125 solo-equivalent credit.
- Với simulator MVP, hiển thị cả tổng objective damage và damage chia đều cho 2 người.

Mode switch:

- User có thể đổi qua lại Solo/Duo.
- Khi đổi từ Duo về Solo, giữ 3 card đầu, card thứ 4 tạm thời inactive.
- Khi đổi lại Duo, restore card thứ 4 nếu còn hợp lệ.

Duplicate cards:

- Cho phép dùng nhiều copy cùng một card trong team.
- Sau này talent engine cần xử lý các talent không được stack bằng `stack_key`.

## 10. RNG Settings

Mỗi round, cả hai phe có RNG:

```txt
Crit chance = 5%
Dodge chance = 1%
Max round = 20
Crit multiplier = 1.75
```

Toggles riêng:

```js
{
  player_crit_enabled: true,
  player_dodge_enabled: true,
  enemy_crit_enabled: true,
  enemy_dodge_enabled: true
}
```

Khuyến nghị MVP:

- Roll dodge trước.
- Nếu dodge proc, bỏ qua crit và damage = 0.
- Nếu không dodge, roll crit.
- Cho phép nhập seed optional để lặp lại simulation.

## 11. Damage Formula

Công thức damage:

```txt
(((team_base_atk / enemy_def) * (team_atk / 2.9) + 220000 / enemy_def) / 3
* elem_multiplier
* crit_multiplier)
```

Trong đó:

```txt
team_base_atk = tổng base ATK của toàn bộ card trong team
team_atk = tổng final ATK của toàn bộ card trong team
enemy_def = final DEF của enemy sau level/evo/asc/difficulty
elem_multiplier = element multiplier của team nhiều hệ
crit_multiplier = 1.75 nếu crit, ngược lại 1
```

Rule:

```txt
Base stats và final stats được cộng lại trước.
Khi vào trận, tất cả stat được nhân 10 trước khi tính damage.
Damage rounding dùng floor.
```

Implementation đề xuất:

```ts
function calculateDamage(input) {
  const teamBaseAtk = input.attacker.base_atk * 10;
  const teamAtk = input.attacker.final_atk * 10;
  const enemyDef = input.defender.final_def * 10;
  const elem = input.element_multiplier ?? 1;
  const crit = input.is_crit ? 1.75 : 1;

  const rawDamage = (((teamBaseAtk / enemyDef) * (teamAtk / 2.9) + 220000 / enemyDef) / 3) * elem * crit;

  return Math.floor(rawDamage);
}
```

Enemy đánh player dùng cùng công thức, chỉ đảo attacker/defender:

```txt
enemy_base_atk vs player_team_def
enemy_final_atk vs player_team_def
enemy_element vs player_team_elements
```

## 12. Element Multiplier

Element multiplier ảnh hưởng trực tiếp vào damage và cần hỗ trợ nhiều card trong player team.

Element list:

```txt
Fire
Water
Electric
Ground
Grass
Neutral
Light
Dark
Null
```

Quan hệ element đã chốt:

```txt
Water khắc Fire
Fire khắc Grass
Grass khắc Ground
Ground khắc Electric
Electric khắc Water
Light và Dark khắc lẫn nhau
```

Multiplier cơ bản:

```txt
Khắc chế: +0.50 relation
Bị khắc: -0.50 relation
Same element: -0.50 relation, trừ Neutral
Neutral với mọi hệ khác: 0 hai chiều, trừ Null
Neutral gây thêm 25% sát thương cho Null: +0.25 relation
Null nhận giảm 15% damage từ tất cả hệ khác, trừ Neutral: -0.15 relation
Null không tăng damage gây ra: 0 relation khi Null là attacker
```

Vì team có nhiều hệ, mỗi relationship được chia theo số familiar và opponent:

```txt
element_multiplier = 1 + sum(relation / (opponent_count * familiar_count))
```

Trong Clan Breach MVP:

```txt
familiar_count = số card trong player team nếu player đang đánh
opponent_count = 1 vì mỗi ván chỉ đánh 1 enemy
```

Khi enemy đánh player:

```txt
familiar_count = 1 vì enemy là 1 unit
opponent_count = số card trong player team
```

Ví dụ raid:

```txt
Player: Water, Fire, Neutral
Boss: Fire

Player multiplier = 1 + 0.5/3 - 0.5/3 + 0/3
```

Implementation đề xuất:

```ts
function calculateElementMultiplier(attackerElements, defenderElements) {
  const familiarCount = attackerElements.length;
  const opponentCount = defenderElements.length;
  let delta = 0;

  for (const attackerElement of attackerElements) {
    for (const defenderElement of defenderElements) {
      const relation = getElementRelation(attackerElement, defenderElement);
      delta += relation / (opponentCount * familiarCount);
    }
  }

  return clamp(1 + delta, 0.5, 1.5);
}
```

`getElementRelation(attacker, defender)` nên dùng adjacency table, không nên hardcode bằng if/else dài.

Ví dụ table dạng data:

```js
const ELEMENT_RELATIONS = {
  Water: { Fire: 0.5, Electric: -0.5, Water: -0.5 },
  Fire: { Grass: 0.5, Water: -0.5, Fire: -0.5 },
  Grass: { Ground: 0.5, Fire: -0.5, Grass: -0.5 },
  Ground: { Electric: 0.5, Grass: -0.5, Ground: -0.5 },
  Electric: { Water: 0.5, Ground: -0.5, Electric: -0.5 },
  Light: { Dark: 0.5, Light: -0.5 },
  Dark: { Light: 0.5, Dark: -0.5 },
  Neutral: { Null: 0.25 },
  Null: {}
};
```

Null defense rule cần apply theo defender:

```ts
function getElementRelation(attacker, defender) {
  if (defender === "Null" && attacker !== "Neutral" && attacker !== "Null") {
    return -0.15;
  }

  return ELEMENT_RELATIONS[attacker]?.[defender] ?? 0;
}
```

Categories hiển thị:

```txt
0.50 - 0.75: Not very effective
0.75 - 1.00: Slightly not effective
1.00 - 1.25: Slightly effective
1.25 - 1.50: Super effective
```

## 13. Simulation Loop MVP

Default MVP simulation:

1. Build player team unit:
   - Solo: cộng stats của 3 card.
   - Duo: cộng stats của 4 card.
   - Lưu danh sách element của từng card để tính element multiplier.
2. Build enemy unit:
   - Main boss hoặc 1 trong 2 herald.
   - Enemy luôn là 1 unit.
   - Apply rarity/evo/asc/level.
   - Apply difficulty multiplier.
3. Chạy tối đa 20 round.
4. Mỗi round:
   - So sánh `player_team.final_spd` và `enemy.final_spd`.
   - Phe có SPD cao hơn đánh trước.
   - Nếu SPD bằng nhau, player đi trước trong MVP.
   - Phe đi trước attack 1 hit.
   - Nếu phe còn lại chưa chết, phe còn lại đánh ngược 1 hit.
   - Mỗi hit roll dodge/crit theo setting của defender/attacker.
   - Tính damage bằng damage formula.
   - Trừ vào HP tổng của target.
5. Dừng nếu player team HP <= 0 hoặc enemy HP <= 0.
6. Trả về summary và round log.

Targeting MVP:

- Player chọn đúng 1 enemy để đánh:
  - Main Boss
  - Herald Of Salvation
  - Herald Of Damnation
- Không có target selection trong enemy side vì player là 1 team unit có 1 thanh HP tổng.
- Không cần track HP event thật. HP trong simulator là HP local cho một simulation run.

Talent:

- Chưa cần làm talent simulator trong MVP.
- Vẫn nên thiết kế hook `applyTalentEffects()` để sau này thêm từng talent.
- Một vài talent không cho phép stack dù dùng nhiều copy cùng card, nên talent engine cần có `stack_key`.

## 14. API Endpoints

Auth:

```txt
GET  /api/auth/discord
GET  /api/auth/discord/callback
POST /api/auth/logout
GET  /api/me
```

Cards:

```txt
GET  /api/cards
GET  /api/cards/:id
GET  /api/bosses
GET  /api/heralds
POST /api/admin/cards/sync
POST /api/admin/bosses/sync-from-clan-shop-series
```

Query params cho `GET /api/cards`:

```txt
search
series
element
talent
last_patch
sort
page
limit
```

User card bag:

```txt
GET    /api/me/cards
POST   /api/me/cards
PATCH  /api/me/cards/:userCardId
DELETE /api/me/cards/:userCardId
```

Add user card payload:

```js
{
  card_master_id: string,
  rarity: "SR" | "UR",
  ascend: 0
}
```

Backend tự set:

```txt
evo = 3
level = 50 nếu SR
level = 60 nếu UR
```

Simulator:

```txt
POST /api/simulate
```

Payload:

```js
{
  mode: "solo" | "duo",
  team_user_card_ids: ["..."],
  enemy_type: "boss" | "herald",
  boss_card_master_id: "...",
  herald_card_master_id: "1170",
  difficulty: "easy" | "medium" | "hard" | "impossible",
  rng: {
    player_crit_enabled: true,
    player_dodge_enabled: true,
    enemy_crit_enabled: true,
    enemy_dodge_enabled: true
  },
  seed: null
}
```

Rules:

- Nếu `enemy_type = "boss"` thì dùng `boss_card_master_id`.
- Nếu `enemy_type = "herald"` thì dùng `herald_card_master_id`, chỉ cho `1170` hoặc `1171`.
- Boss card phải thuộc series clan shop.

Response:

```js
{
  summary: {
    mode: "solo",
    difficulty: "medium",
    enemy_name: "World-Ender",
    total_player_damage: 1234567,
    total_enemy_damage: 222222,
    rounds_used: 20,
    enemy_remaining_hp: 999999,
    player_team_remaining_hp: 888888,
    enemy_defeated: false,
    player_team_defeated: false,
    turn_order_rule: "higher_spd_first",
    player_element_multiplier: 1.08,
    enemy_element_multiplier: 0.92
  },
  team_stats: {
    base_hp: 100,
    base_atk: 100,
    base_def: 100,
    base_spd: 100,
    final_hp: 400,
    final_atk: 400,
    final_def: 400,
    final_spd: 400
  },
  duo_credit: {
    objective_damage: 1234567,
    caller_credit: 617283,
    teammate_credit: 617284
  },
  round_log: [
    {
      round: 1,
      actor: "player",
      target: "enemy",
      damage: 1234,
      crit: false,
      dodged: false,
      element_multiplier: 1.08,
      target_remaining_hp: 999999
    }
  ]
}
```

## 15. Frontend Pages

### Login Page

- Discord login button.
- Nếu đã login thì redirect vào dashboard.

### Dashboard

- Quick stats:
  - Số card trong túi.
  - Last database sync.
  - Saved simulator presets gần đây.
- CTA:
  - My Cards
  - Simulator

### My Cards

Chức năng:

- Xem card bag của user.
- Add card.
- Edit rarity/ascend.
- Delete card.

Add card modal:

- Search input.
- Filter series.
- Filter element.
- Filter talent.
- Card result list có art, name, series, element, base stats.
- Chọn rarity SR/UR.
- Chọn ascend theo rarity.
- Level và Evo hiện read-only:
  - SR level 50 E3
  - UR level 60 E3

### Simulator

Controls:

- Mode segmented control: Solo / Duo.
- Team slots:
  - Solo: 3 slots.
  - Duo: 4 slots.
- Enemy selector:
  - Main Boss
  - Herald Of Salvation
  - Herald Of Damnation
- Boss selector chỉ hiện card thuộc clan shop series.
- Difficulty selector.
- RNG toggles.
- Simulate button.

Results:

- Total player damage.
- Total enemy damage.
- Duo credit nếu đang ở duo mode.
- Rounds used.
- Crit/dodge counts.
- Enemy remaining HP.
- Player team remaining HP.
- Player/enemy element multiplier.
- Round log collapsible.

### Boss Admin

Chỉ cần nếu web có admin panel:

- Đánh dấu card nào trong database thuộc clan shop và có thể làm main boss.
- Có thể auto-sync boss list bằng series clan shop.
- Chọn boss active theo mùa nếu muốn.

### Card Database

Optional trong MVP, nhưng hữu ích:

- Browse all cards.
- Xem base stats.
- Xem calculated stats với rarity/asc/evo/level.
- Copy/add vào bag.

## 16. Presets

Cho phép user lưu simulator setup để dùng lại.

```js
{
  id: string,
  user_id: string,
  name: string,
  mode: "solo" | "duo",
  team_user_card_ids: string[],
  enemy_type: "boss" | "herald",
  boss_card_master_id: string | null,
  herald_card_master_id: "1170" | "1171" | null,
  difficulty: "easy" | "medium" | "hard" | "impossible",
  rng: {
    player_crit_enabled: boolean,
    player_dodge_enabled: boolean,
    enemy_crit_enabled: boolean,
    enemy_dodge_enabled: boolean
  },
  created_at: Date,
  updated_at: Date
}
```

MVP có thể chưa cần presets nếu muốn code nhanh.

## 17. Validation Rules

User card:

- `rarity` chỉ được SR/UR.
- SR ascend 0-4.
- UR ascend 0-5.
- Evo fixed 3.
- Level tự động theo rarity.

Simulator:

- Solo phải có đúng 3 cards.
- Duo phải có đúng 4 cards.
- Cho phép dùng nhiều copy cùng một card trong team nếu user có nhiều card instance hoặc chọn cùng card ở simulator sandbox.
- Difficulty bắt buộc hợp lệ.
- Enemy type bắt buộc hợp lệ.
- Boss card bắt buộc tồn tại và phải thuộc series clan shop.
- Herald card chỉ được là ID `1170` hoặc `1171`.
- Player team và enemy đều phải có HP/ATK/DEF/SPD final > 0.

## 18. Security và Rate Limit

- Discord OAuth secret chỉ nằm ở backend.
- Session cookie nên `HttpOnly`, `Secure`, `SameSite=Lax`.
- Rate limit:
  - `/api/simulate`
  - `/api/cards`
  - auth callback
- Không expose Google Sheets API key nếu không cần.
- Cache card API để tránh spam Google Sheets.

## 19. Tech Stack Đề Xuất

Nếu build gần với repo Python hiện tại:

- Backend: FastAPI hoặc Flask.
- Auth: Discord OAuth2.
- Database: MongoDB hiện có.
- Frontend: React + Vite.
- Styling: Tailwind hoặc CSS module.

Nếu build tách riêng:

- Backend: Node.js/NestJS hoặc FastAPI.
- Frontend: Next.js.
- Database: MongoDB/Postgres.

Vì bot hiện tại đã dùng MongoDB, phương án dễ reuse nhất:

```txt
FastAPI + MongoDB + React/Vite
```

## 20. Milestones

### Milestone 1: Card API

- Fetch Google Sheet CSV.
- Parse cards.
- Save normalized card master.
- `GET /api/cards` có search/filter/sort.
- Tạo boss list từ series clan shop.
- Verify herald ID `1170` và `1171` có trong card database.

### Milestone 2: Discord Login

- OAuth login/logout.
- `GET /api/me`.
- Session handling.

### Milestone 3: My Cards

- Add card vào bag.
- Edit rarity/ascend.
- Delete card.
- Calculate final stats.

### Milestone 4: Simulator MVP

- Solo/Duo team selector.
- Team-unit stat aggregation.
- Boss/herald selector.
- Difficulty selector.
- RNG toggles.
- Enemy đánh ngược lại player.
- SPD quyết định phe đi trước.
- Element multiplier cho team nhiều hệ.
- Damage formula + floor rounding.
- Summary + round log.

### Milestone 5: Polish

- Save presets.
- Better result charts.
- Import/export team.
- Talent handling chi tiết.
- Talent stack rules.

## 21. Open Questions

- Có cần seed RNG hiển thị trên UI để user share/reproduce kết quả không?
- Khi SPD bằng nhau, chốt player đi trước hay random theo seed?
- Có cần simulator sandbox cho phép chọn card ngoài túi không, hay bắt buộc phải add vào túi trước?
- Có cần cho user tự override boss/herald level để test ngoài chuẩn 1400/900 không?
- Talent nào cần ưu tiên làm trước sau MVP?
