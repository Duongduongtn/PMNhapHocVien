# In Báo cáo 2 (TNB-08, task 166) — dựng PDF bằng chính mẫu rptBaoCao2.rpt + bộ Crystal Reports của phần mềm cũ.
# Chạy bằng PowerShell 32-bit (SysWOW64): các dll Crystal của phần mềm cũ là 32-bit.
# Đọc JSON dữ liệu (2 bảng đúng tên cột của usp_BaoCao_TieuDe, usp_BaoCao2_ViewRPT) → đẩy vào mẫu → xuất PDF.
# Mẫu .rpt chỉ được đọc từ thư mục phần mềm cũ trên máy (OpenReportByTempCopy: không sửa tệp gốc).
param(
  [Parameter(Mandatory = $true)][string]$Rpt,
  [Parameter(Mandatory = $true)][string]$Json,
  [Parameter(Mandatory = $true)][string]$Pdf,
  [Parameter(Mandatory = $true)][string]$CrystalDir
)
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

[void][Reflection.Assembly]::LoadFrom("$CrystalDir\CrystalDecisions.Shared.dll")
[void][Reflection.Assembly]::LoadFrom("$CrystalDir\CrystalDecisions.ReportSource.dll")
[void][Reflection.Assembly]::LoadFrom("$CrystalDir\CrystalDecisions.CrystalReports.Engine.dll")

$d = [IO.File]::ReadAllText($Json, [Text.Encoding]::UTF8) | ConvertFrom-Json

# Kiểu cột suy từ giá trị; cột chỉ có null → chuỗi (cùng cách phần mềm cũ nhận từ SP).
function Kieu($rows, $ten) {
  # Duyệt MỌI dòng: dòng đầu là 0 mà dòng sau là 1.5 thì cột phải là số thực, không làm tròn lặng lẽ.
  $coInt = $false; $coSoThuc = $false; $kieu = $null
  foreach ($r in $rows) {
    $v = $r.$ten
    if ($null -eq $v) { continue }
    if ($v -is [bool]) { $kieu = [bool]; continue }
    if ($v -is [int] -or $v -is [long]) { $coInt = $true; continue }
    if ($v -is [double] -or $v -is [decimal]) { $coSoThuc = $true; continue }
    if ($v -is [string] -and $v -match '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}') { $kieu = [datetime]; continue }
    return [string]
  }
  if ($kieu) { return $kieu }
  if ($coSoThuc) { return [decimal] }
  if ($coInt) { return [int] }
  return [string]
}

function BangTu($ten, $rows) {
  $t = New-Object System.Data.DataTable $ten
  if ($rows.Count -eq 0) { return , $t }
  foreach ($p in $rows[0].PSObject.Properties) { [void]$t.Columns.Add($p.Name, (Kieu $rows $p.Name)) }
  foreach ($r in $rows) {
    $row = $t.NewRow()
    foreach ($c in $t.Columns) {
      $v = $r.($c.ColumnName)
      if ($null -eq $v) { $row[$c.ColumnName] = [DBNull]::Value }
      elseif ($c.DataType -eq [datetime]) { $row[$c.ColumnName] = [datetime]::Parse($v) }
      else { $row[$c.ColumnName] = $v }
    }
    $t.Rows.Add($row)
  }
  return , $t
}

$ds = New-Object System.Data.DataSet
$ds.Tables.Add((BangTu "usp_BaoCao_TieuDe;1" @($d.tieu_de)))
$ds.Tables.Add((BangTu "usp_BaoCao2_ViewRPT;1" @($d.dong)))

$r = New-Object CrystalDecisions.CrystalReports.Engine.ReportDocument
try {
  $r.Load($Rpt, [CrystalDecisions.Shared.OpenReportMethod]::OpenReportByTempCopy)
  $r.SetDataSource($ds)
  # Crystal bỏ tham số của SP khi đẩy DataSet → công thức {?@...} thay bằng hằng chuỗi (chỉ trên bản sao tạm).
  $gt = @{ "@MaKH" = [string]$d.ma_kh; "@MaBC2" = [string]$d.ma_bc2; "@Loai" = "2" }
  foreach ($f in $r.DataDefinition.FormulaFields) {
    $txt = $f.Text
    foreach ($k in $gt.Keys) {
      $mau = [regex]::Escape("{?" + $k + "}")
      $thay = ('"' + $gt[$k].Replace('"', '""') + '"').Replace('$', '$$')
      $txt = [regex]::Replace($txt, $mau, $thay, [Text.RegularExpressions.RegexOptions]::IgnoreCase)
    }
    if ($txt -ne $f.Text) { $f.Text = $txt }
  }
  $r.ExportToDisk([CrystalDecisions.Shared.ExportFormatType]::PortableDocFormat, $Pdf)
  "OK " + (Get-Item -LiteralPath $Pdf).Length
}
finally {
  $r.Close()
  $r.Dispose()
}
