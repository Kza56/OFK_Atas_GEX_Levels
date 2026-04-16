// ============================================================================
//  OFK_ES_GEX_Levels.cs — ATAS
//  Lit full_levels_ES.json et affiche tous les niveaux GEX + Options ES.
//
//  Niveaux chart : Gamma Flip, Vol Trigger, Call Wall, Put Wall, Risk Pivot,
//                  Vanna Flip, Charm Magnet, Max Pain, EM High, EM Low,
//                  Top OI #1, Top OI #2, Top OI #3
//
//  Panel : GEX LEVELS (run_morning_ES.py) + Briefing (ouvre PDF ES)
// ============================================================================
using System;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using ATAS.Indicators;
using OFT.Rendering.Context;
using OFT.Rendering.Tools;
using DrawingColor = System.Drawing.Color;

namespace OFK_Suite
{
    [DisplayName("OFK ES GEX Levels")]
    [Category("OFK Suite")]
    [Description("Niveaux Greeks Options ES. Lit full_levels_ES.json.")]
    public class OFK_ES_GEX_Levels : Indicator
    {
        #region Snapshot

        private sealed class GexSnapshot
        {
            public readonly double GammaFlip, VolTrigger, CallWall, PutWall;
            public readonly double RiskPivot, VannaFlip, CharmMagnet;
            public readonly double MaxPain, ExpectedMoveHigh, ExpectedMoveLow, ExpectedMovePts;
            public readonly double TopOI1, TopOI2, TopOI3;
            public readonly long   TopOI1Vol, TopOI2Vol, TopOI3Vol;
            public readonly double Pcr;
            public readonly double CallWallGex, PutWallGex;
            public readonly double GexTotal, VexTotal, CexTotal, DexTotal, SpotLoaded;
            public readonly int    GexRegime, VexRegime;
            public readonly string TradeDate;
            public readonly bool   Loaded;

            public static readonly GexSnapshot Empty = new GexSnapshot(
                0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,"",false);

            public GexSnapshot(
                double gammaFlip, double volTrigger, double callWall, double putWall,
                double riskPivot, double vannaFlip,  double charmMagnet,
                double maxPain,   double emHigh,     double emLow,     double emPts,
                double topOI1,    double topOI2,     double topOI3,
                long   topOI1Vol, long   topOI2Vol,  long   topOI3Vol,
                double pcr,       double callWallGex, double putWallGex,
                double gexTotal,  double vexTotal,   double cexTotal,  double dexTotal,
                double spotLoaded, int gexRegime,    int vexRegime,
                string tradeDate, bool loaded)
            {
                GammaFlip        = gammaFlip;
                VolTrigger       = volTrigger;
                CallWall         = callWall;
                PutWall          = putWall;
                RiskPivot        = riskPivot;
                VannaFlip        = vannaFlip;
                CharmMagnet      = charmMagnet;
                MaxPain          = maxPain;
                ExpectedMoveHigh = emHigh;
                ExpectedMoveLow  = emLow;
                ExpectedMovePts  = emPts;
                TopOI1           = topOI1;
                TopOI2           = topOI2;
                TopOI3           = topOI3;
                TopOI1Vol        = topOI1Vol;
                TopOI2Vol        = topOI2Vol;
                TopOI3Vol        = topOI3Vol;
                Pcr              = pcr;
                CallWallGex      = callWallGex;
                PutWallGex       = putWallGex;
                GexTotal         = gexTotal;
                VexTotal         = vexTotal;
                CexTotal         = cexTotal;
                DexTotal         = dexTotal;
                SpotLoaded       = spotLoaded;
                GexRegime        = gexRegime;
                VexRegime        = vexRegime;
                TradeDate        = tradeDate ?? "";
                Loaded           = loaded;
            }
        }

        #endregion

        #region 01.Source

        [Display(Name = "JSON Path", GroupName = "01.Source", Order = 1)]
        public string JsonPath { get; set; } = @"C:\gex_agent\data\full_levels_ES.json";

        [Display(Name = "Refresh (minutes)", GroupName = "01.Source", Order = 2)]
        [Range(1, 240)]
        public int RefreshMinutes { get; set; } = 30;

        #endregion

        #region 02.Niveaux GEX

        [Display(Name = "Gamma Flip",            GroupName = "02.Niveaux GEX", Order = 1)]
        public bool ShowGammaFlip   { get; set; } = true;
        [Display(Name = "Vol Trigger",           GroupName = "02.Niveaux GEX", Order = 2)]
        public bool ShowVolTrigger  { get; set; } = true;
        [Display(Name = "Call Wall",             GroupName = "02.Niveaux GEX", Order = 3)]
        public bool ShowCallWall    { get; set; } = true;
        [Display(Name = "Put Wall",              GroupName = "02.Niveaux GEX", Order = 4)]
        public bool ShowPutWall     { get; set; } = true;
        [Display(Name = "Risk Pivot (trapdoor)", GroupName = "02.Niveaux GEX", Order = 5)]
        public bool ShowRiskPivot   { get; set; } = true;

        #endregion

        #region 03.Niveaux VEX/CEX

        [Display(Name = "Vanna Flip",                      GroupName = "03.Niveaux VEX/CEX", Order = 1)]
        public bool ShowVannaFlip   { get; set; } = false;
        [Display(Name = "Charm Magnet (0DTE fin session)", GroupName = "03.Niveaux VEX/CEX", Order = 2)]
        public bool ShowCharmMagnet { get; set; } = false;

        #endregion

        #region 04.Niveaux Options

        [Display(Name = "Max Pain",           GroupName = "04.Niveaux Options", Order = 1)]
        public bool ShowMaxPain          { get; set; } = true;
        [Display(Name = "Expected Move High", GroupName = "04.Niveaux Options", Order = 2)]
        public bool ShowExpectedMoveHigh  { get; set; } = true;
        [Display(Name = "Expected Move Low",  GroupName = "04.Niveaux Options", Order = 3)]
        public bool ShowExpectedMoveLow   { get; set; } = true;
        [Display(Name = "Zone EM (fond)",     GroupName = "04.Niveaux Options", Order = 4)]
        public bool ShowEMZone            { get; set; } = false;

        #endregion

        #region 05.Niveaux Top OI

        [Display(Name = "Top OI #1 (plus gros strike)", GroupName = "05.Niveaux Top OI", Order = 1)]
        public bool ShowTopOI1 { get; set; } = true;
        [Display(Name = "Top OI #2",                    GroupName = "05.Niveaux Top OI", Order = 2)]
        public bool ShowTopOI2 { get; set; } = true;
        [Display(Name = "Top OI #3",                    GroupName = "05.Niveaux Top OI", Order = 3)]
        public bool ShowTopOI3 { get; set; } = true;

        #endregion

        #region 06.Visuel

        [Display(Name = "Zone pinning Call/Put Wall", GroupName = "06.Visuel", Order = 1)]
        public bool ShowPinZone   { get; set; } = false;
        [Display(Name = "Epaisseur lignes",           GroupName = "06.Visuel", Order = 2)]
        [Range(1, 5)]
        public int  LineWidth     { get; set; } = 2;
        [Display(Name = "Taille police labels",       GroupName = "06.Visuel", Order = 3)]
        [Range(7, 14)]
        public int  LabelFontSize { get; set; } = 9;
        [Display(Name = "Opacité zone pinning %",     GroupName = "06.Visuel", Order = 4)]
        [Range(1, 40)]
        public int  PinZoneOpacity { get; set; } = 8;

        #endregion

        #region 07.Couleurs GEX

        [Display(Name = "Gamma Flip",   GroupName = "07.Couleurs GEX", Order = 1)]
        public DrawingColor GammaFlipColor   { get; set; } = DrawingColor.Yellow;
        [Display(Name = "Vol Trigger",  GroupName = "07.Couleurs GEX", Order = 2)]
        public DrawingColor VolTriggerColor  { get; set; } = DrawingColor.Gold;
        [Display(Name = "Call Wall",    GroupName = "07.Couleurs GEX", Order = 3)]
        public DrawingColor CallWallColor    { get; set; } = DrawingColor.LimeGreen;
        [Display(Name = "Put Wall",     GroupName = "07.Couleurs GEX", Order = 4)]
        public DrawingColor PutWallColor     { get; set; } = DrawingColor.OrangeRed;
        [Display(Name = "Risk Pivot",   GroupName = "07.Couleurs GEX", Order = 5)]
        public DrawingColor RiskPivotColor   { get; set; } = DrawingColor.Crimson;
        [Display(Name = "Vanna Flip",   GroupName = "07.Couleurs GEX", Order = 6)]
        public DrawingColor VannaFlipColor   { get; set; } = DrawingColor.Violet;
        [Display(Name = "Charm Magnet", GroupName = "07.Couleurs GEX", Order = 7)]
        public DrawingColor CharmMagnetColor { get; set; } = DrawingColor.CornflowerBlue;

        #endregion

        #region 08.Couleurs Options

        [Display(Name = "Max Pain",           GroupName = "08.Couleurs Options", Order = 1)]
        public DrawingColor MaxPainColor          { get; set; } = DrawingColor.Gray;
        [Display(Name = "Expected Move High", GroupName = "08.Couleurs Options", Order = 2)]
        public DrawingColor ExpectedMoveHighColor { get; set; } = DrawingColor.MediumAquamarine;
        [Display(Name = "Expected Move Low",  GroupName = "08.Couleurs Options", Order = 3)]
        public DrawingColor ExpectedMoveLowColor  { get; set; } = DrawingColor.MediumAquamarine;
        [Display(Name = "Top OI #1",          GroupName = "08.Couleurs Options", Order = 4)]
        public DrawingColor TopOI1Color           { get; set; } = DrawingColor.FromArgb(255, 100, 180, 255);
        [Display(Name = "Top OI #2",          GroupName = "08.Couleurs Options", Order = 5)]
        public DrawingColor TopOI2Color           { get; set; } = DrawingColor.FromArgb(200, 100, 180, 255);
        [Display(Name = "Top OI #3",          GroupName = "08.Couleurs Options", Order = 6)]
        public DrawingColor TopOI3Color           { get; set; } = DrawingColor.FromArgb(150, 100, 180, 255);

        #endregion

        #region 09.Panel flottant

        [Display(Name = "Afficher panneau", GroupName = "09.Panel flottant", Order = 1)]
        public bool ShowPanel
        {
            get => _showPanel;
            set
            {
                _showPanel = value;
                Application.Current?.Dispatcher?.BeginInvoke(new Action(() =>
                {
                    if (_showPanel  && !_panelOpen) OpenPanel();
                    else if (!_showPanel && _panelOpen) ClosePanel();
                }));
            }
        }
        private bool _showPanel = true;

        [Display(Name = "Chemin Python (exe)", GroupName = "09.Panel flottant", Order = 2)]
        public string PythonExePath { get; set; } = @"C:\Python314\python.exe";

        [Display(Name = "Chemin script .py", GroupName = "09.Panel flottant", Order = 3)]
        public string ScriptPath { get; set; } = @"C:\gex_agent\run_morning_ES.py";

        [Display(Name = "Dossier PDF briefing", GroupName = "09.Panel flottant", Order = 4)]
        public string BriefingDir { get; set; } = @"C:\gex_agent\data";

        #endregion

        #region Private

        private volatile GexSnapshot _levels      = GexSnapshot.Empty;
        private string   _loadedDate  = "";
        private bool     _levelsLoaded = false;
        private DateTime _lastLoadTime = DateTime.MinValue;

        private readonly RenderFont _font = new RenderFont("Arial", 9);

        private Window    _panelWindow = null;
        private TextBlock _infoText    = null;
        private Button    _btnRefresh  = null;
        private Button    _btnBriefing = null;
        private TextBlock _statusText  = null;
        private bool      _isRunning   = false;
        private bool      _panelOpen   = false;

        #endregion

        public OFK_ES_GEX_Levels() : base(true)
        {
            EnableCustomDrawing = true;
            SubscribeToDrawingEvents(DrawingLayouts.Historical | DrawingLayouts.LatestBar | DrawingLayouts.Final);
            DenyToChangePanel = true;
            DataSeries[0].IsHidden = true;
            ((ValueDataSeries)DataSeries[0]).VisualType = VisualMode.Hide;
        }

        protected override void OnCalculate(int bar, decimal value)
        {
            if (bar == 0)
            {
                if (!_levelsLoaded) LoadLevels();
                Application.Current?.Dispatcher?.BeginInvoke(new Action(() =>
                {
                    if (ShowPanel && !_panelOpen) OpenPanel();
                }));
            }
            if (!_levelsLoaded) return;

            bool isLastBar = bar >= CurrentBar - 1;
            bool newDay    = _loadedDate != DateTime.Today.ToString("yyyy-MM-dd");
            bool elapsed   = RefreshMinutes > 0 &&
                             (DateTime.Now - _lastLoadTime).TotalMinutes >= RefreshMinutes;
            if (isLastBar && (newDay || elapsed)) { LoadLevels(); UpdatePanelText(); }
        }

        // ── Panel ─────────────────────────────────────────────────────────────

        private void OpenPanel()
        {
            if (_panelOpen) return;
            var lv = _levels;

            var bgColor      = System.Windows.Media.Color.FromRgb(22, 27, 39);
            var bgDark       = System.Windows.Media.Color.FromRgb(13, 17, 23);
            var borderColor  = System.Windows.Media.Color.FromRgb(33, 41, 61);
            var textColor    = System.Windows.Media.Color.FromRgb(201, 209, 217);
            var textDimColor = System.Windows.Media.Color.FromRgb(139, 148, 158);
            var accentBlue   = System.Windows.Media.Color.FromRgb(79, 139, 209);

            _panelWindow = new Window
            {
                Title = "OFK ES GEX Levels", Width = 430,
                SizeToContent = SizeToContent.Height, Topmost = true,
                ResizeMode = ResizeMode.CanResizeWithGrip,
                WindowStartupLocation = WindowStartupLocation.Manual,
                Left = 80, Top = 80,
                Background = new SolidColorBrush(bgColor),
                ShowInTaskbar = false,
                FontFamily = new System.Windows.Media.FontFamily("Segoe UI"),
                FontSize = 12,
            };

            var root  = new Border { Background = new SolidColorBrush(bgColor), BorderBrush = new SolidColorBrush(borderColor), BorderThickness = new Thickness(1) };
            var outer = new StackPanel();

            // Header
            var hdr = new Border { Background = new SolidColorBrush(bgDark), BorderBrush = new SolidColorBrush(borderColor), BorderThickness = new Thickness(0,0,0,1), Padding = new Thickness(12,8,12,8) };
            hdr.Child = new TextBlock { Text = "OFK ES GEX Levels", Foreground = new SolidColorBrush(accentBlue), FontSize = 13, FontWeight = FontWeights.SemiBold };
            outer.Children.Add(hdr);

            // Info text
            var infoSec = new Border { Background = new SolidColorBrush(System.Windows.Media.Color.FromRgb(18,22,30)), Padding = new Thickness(12,10,12,10), BorderBrush = new SolidColorBrush(borderColor), BorderThickness = new Thickness(0,0,0,1) };
            _infoText = new TextBlock { FontFamily = new System.Windows.Media.FontFamily("Consolas"), FontSize = 11, Foreground = new SolidColorBrush(textColor), TextWrapping = TextWrapping.NoWrap, LineHeight = 18 };
            infoSec.Child = _infoText;
            outer.Children.Add(infoSec);

            // Boutons
            var btnSec = new Border { Padding = new Thickness(12,8,12,8), BorderBrush = new SolidColorBrush(borderColor), BorderThickness = new Thickness(0,0,0,1) };
            var grid = new Grid();
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(8) });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });

            _btnRefresh = new Button
            {
                Content = "▶  GEX LEVELS ES", Height = 32,
                Background = new SolidColorBrush(System.Windows.Media.Color.FromRgb(20,40,90)),
                Foreground = new SolidColorBrush(accentBlue),
                FontSize = 11, FontFamily = new System.Windows.Media.FontFamily("Segoe UI"),
                FontWeight = FontWeights.SemiBold,
                BorderBrush = new SolidColorBrush(System.Windows.Media.Color.FromRgb(79,139,209)),
                BorderThickness = new Thickness(1), Cursor = System.Windows.Input.Cursors.Hand,
                Template = CreateButtonTemplate(),
            };
            _btnRefresh.Click += (s, e) => RunScript();
            Grid.SetColumn(_btnRefresh, 0);
            grid.Children.Add(_btnRefresh);

            _btnBriefing = new Button
            {
                Content = "📄  Briefing", Height = 32,
                Background = new SolidColorBrush(System.Windows.Media.Color.FromRgb(20,55,40)),
                Foreground = new SolidColorBrush(System.Windows.Media.Color.FromRgb(63,185,80)),
                FontSize = 11, FontFamily = new System.Windows.Media.FontFamily("Segoe UI"),
                FontWeight = FontWeights.SemiBold,
                BorderBrush = new SolidColorBrush(System.Windows.Media.Color.FromRgb(63,185,80)),
                BorderThickness = new Thickness(1), Cursor = System.Windows.Input.Cursors.Hand,
                Template = CreateButtonTemplate(),
            };
            _btnBriefing.Click += (s, e) => OpenBriefing();
            Grid.SetColumn(_btnBriefing, 2);
            grid.Children.Add(_btnBriefing);

            btnSec.Child = grid;
            outer.Children.Add(btnSec);

            // Status
            var statusSec = new Border { Background = new SolidColorBrush(bgDark), Padding = new Thickness(12,5,12,5) };
            _statusText = new TextBlock { FontFamily = new System.Windows.Media.FontFamily("Segoe UI"), FontSize = 10, Foreground = new SolidColorBrush(textDimColor), Text = lv.Loaded ? $"✅ JSON chargé — {lv.TradeDate}  (spot {lv.SpotLoaded:F0})" : "⚠ JSON non chargé — vérifier JSON Path" };
            statusSec.Child = _statusText;
            outer.Children.Add(statusSec);

            root.Child = outer;
            _panelWindow.Content = root;
            _panelWindow.Closed += (s, e) => { _panelOpen = false; _panelWindow = null; _infoText = null; _btnRefresh = null; _btnBriefing = null; _statusText = null; };
            UpdatePanelText();
            _panelWindow.Show();
            _panelOpen = true;
        }

        private void ClosePanel() { _panelWindow?.Close(); _panelOpen = false; }

        private void UpdatePanelText()
        {
            if (_infoText == null) return;
            Application.Current?.Dispatcher?.BeginInvoke(new Action(() =>
            {
                if (_infoText == null) return;
                var lv = _levels;

                string gReg  = lv.GexRegime > 0 ? "POSITIF ● pinning" : lv.GexRegime < 0 ? "NEGATIF ● explosif" : "NEUTRE";
                string vReg  = lv.VexRegime > 0 ? "IV↓ = RALLY ▲"     : lv.VexRegime < 0 ? "IV↑ = SELLOFF ▼"   : "neutre";
                string dSide = lv.DexTotal  > 0 ? "longs" : "shorts";
                string pcrStr= lv.Pcr > 0 ? $"{lv.Pcr:F3}  ({(lv.Pcr > 1 ? "put-heavy" : "call-heavy")})" : "—";
                string emStr = lv.ExpectedMovePts > 0 ? $"±{lv.ExpectedMovePts:F0} pts  [{lv.ExpectedMoveLow:F0} — {lv.ExpectedMoveHigh:F0}]" : "—";
                string oi1   = lv.TopOI1 > 0 ? $"  Top OI #1   {lv.TopOI1:F0}  (OI {lv.TopOI1Vol:N0})\n" : "";
                string oi2   = lv.TopOI2 > 0 ? $"  Top OI #2   {lv.TopOI2:F0}  (OI {lv.TopOI2Vol:N0})\n" : "";
                string oi3   = lv.TopOI3 > 0 ? $"  Top OI #3   {lv.TopOI3:F0}  (OI {lv.TopOI3Vol:N0})\n" : "";

                _infoText.Text =
                    $"═══ OPTIONS GREEKS ES  ({lv.TradeDate}) ═══\n\n" +
                    $"  GEX  {lv.GexTotal / 1e9:+0.000;-0.000}B   {gReg}\n" +
                    $"  VEX  {lv.VexTotal / 1e8:+0.00;-0.00}       {vReg}\n" +
                    $"  CEX  {lv.CexTotal / 1e6:+0.00;-0.00}M\n" +
                    $"  DEX  {lv.DexTotal / 1e10:+0.000;-0.000}   dealers {dSide}\n\n" +
                    $"  Gamma Flip  {lv.GammaFlip:F0}     Trigger  {lv.VolTrigger:F0}\n" +
                    $"  Call Wall   {lv.CallWall:F0}     Put Wall {lv.PutWall:F0}\n" +
                    $"  Risk Pivot  {lv.RiskPivot:F0}    V-Flip   {lv.VannaFlip:F0}\n" +
                    $"  Charm       {lv.CharmMagnet:F0}     Spot réf. {lv.SpotLoaded:F0}\n\n" +
                    $"  Max Pain    {lv.MaxPain:F0}\n" +
                    $"  Exp. Move   {emStr}\n" +
                    $"  PCR         {pcrStr}\n\n" +
                    oi1 + oi2 + oi3;

                if (_statusText != null)
                    _statusText.Text = lv.Loaded
                        ? $"✅ JSON chargé — {lv.TradeDate}  (spot {lv.SpotLoaded:F0})"
                        : "⚠ JSON non chargé — vérifier JSON Path";
            }));
        }

        // ── RunScript ─────────────────────────────────────────────────────────

        private void RunScript()
        {
            if (_isRunning) return;
            if (!File.Exists(ScriptPath))
            {
                Application.Current?.Dispatcher?.Invoke(() => { if (_statusText != null) _statusText.Text = "❌ Script introuvable : " + ScriptPath; });
                return;
            }
            _isRunning = true;
            Application.Current?.Dispatcher?.Invoke(() =>
            {
                if (_btnRefresh  != null) { _btnRefresh.Content = "⏳ En cours…"; _btnRefresh.Background = new SolidColorBrush(System.Windows.Media.Color.FromArgb(220,80,60,0)); _btnRefresh.Foreground = System.Windows.Media.Brushes.Orange; _btnRefresh.IsEnabled = false; }
                if (_btnBriefing != null) _btnBriefing.IsEnabled = false;
                if (_statusText  != null) _statusText.Text = "⏳ run_morning_ES.py en cours (CME ES + CBOE SPY + Claude + PDF)…";
            });
            Task.Run(() =>
            {
                try
                {
                    var psi = new ProcessStartInfo
                    {
                        FileName         = PythonExePath,
                        Arguments        = "\"" + ScriptPath + "\"",
                        UseShellExecute  = false,
                        CreateNoWindow   = false,
                        WindowStyle      = ProcessWindowStyle.Normal,
                        WorkingDirectory = System.IO.Path.GetDirectoryName(ScriptPath) ?? @"C:\gex_agent",
                    };
                    using var proc = Process.Start(psi);
                    bool exited = proc?.WaitForExit(300_000) ?? false;
                    int exitCode = exited ? (proc?.ExitCode ?? -1) : -99;
                    if (exitCode == 0) LoadLevels();
                    Application.Current?.Dispatcher?.Invoke(() =>
                    {
                        string msg = exitCode == 0 ? "✅ Données mises à jour" : $"⚠ Exit {exitCode}";
                        if (_btnRefresh  != null) { _btnRefresh.Content = "▶  GEX LEVELS ES"; _btnRefresh.Background = new SolidColorBrush(System.Windows.Media.Color.FromRgb(20,40,90)); _btnRefresh.Foreground = new SolidColorBrush(System.Windows.Media.Color.FromRgb(79,139,209)); _btnRefresh.IsEnabled = true; }
                        if (_btnBriefing != null) _btnBriefing.IsEnabled = true;
                        var lv = _levels;
                        if (_statusText != null) _statusText.Text = msg + (exitCode == 0 ? $"  —  {lv.TradeDate}" : "");
                        UpdatePanelText();
                    });
                    RedrawChart();
                }
                catch (Exception ex)
                {
                    Application.Current?.Dispatcher?.Invoke(() =>
                    {
                        if (_btnRefresh  != null) { _btnRefresh.Content = "▶  GEX LEVELS ES"; _btnRefresh.IsEnabled = true; }
                        if (_btnBriefing != null) _btnBriefing.IsEnabled = true;
                        if (_statusText  != null) _statusText.Text = "❌ " + ex.Message.Substring(0, Math.Min(60, ex.Message.Length));
                    });
                }
                finally { _isRunning = false; }
            });
        }

        // ── OpenBriefing ──────────────────────────────────────────────────────

        private void OpenBriefing()
        {
            try
            {
                if (!Directory.Exists(BriefingDir)) { if (_statusText != null) Application.Current?.Dispatcher?.Invoke(() => _statusText.Text = "❌ Dossier PDF introuvable : " + BriefingDir); return; }
                var pdfs = Directory.GetFiles(BriefingDir, "briefing_ES_*.pdf").OrderByDescending(f => f).ToArray();
                if (pdfs.Length == 0) { if (_statusText != null) Application.Current?.Dispatcher?.Invoke(() => _statusText.Text = "⚠ Aucun PDF trouvé"); return; }
                Process.Start(new ProcessStartInfo(pdfs[0]) { UseShellExecute = true });
                if (_statusText != null) Application.Current?.Dispatcher?.Invoke(() => _statusText.Text = "📄 " + Path.GetFileName(pdfs[0]));
            }
            catch (Exception ex) { if (_statusText != null) Application.Current?.Dispatcher?.Invoke(() => _statusText.Text = "❌ " + ex.Message.Substring(0, Math.Min(60, ex.Message.Length))); }
        }

        // ── Rendu chart ───────────────────────────────────────────────────────

        protected override void OnRender(RenderContext context, DrawingLayouts layout)
        {
            var lv = _levels;
            if (!lv.Loaded || ChartInfo == null) return;
            int chartW = ChartArea.Width;

            // Zone pinning
            if (ShowPinZone && lv.GexRegime > 0 && lv.CallWall > 0 && lv.PutWall > 0)
            {
                int yCw = (int)ChartInfo.GetYByPrice((decimal)lv.CallWall, false);
                int yPw = (int)ChartInfo.GetYByPrice((decimal)lv.PutWall,  false);
                if (yCw < yPw) context.FillRectangle(DrawingColor.FromArgb(PinZoneOpacity * 255 / 100, 0, 200, 0), new Rectangle(0, yCw, chartW, yPw - yCw));
            }

            // Zone Expected Move
            if (ShowEMZone && lv.ExpectedMoveHigh > 0 && lv.ExpectedMoveLow > 0)
            {
                int yH = (int)ChartInfo.GetYByPrice((decimal)lv.ExpectedMoveHigh, false);
                int yL = (int)ChartInfo.GetYByPrice((decimal)lv.ExpectedMoveLow,  false);
                if (yH < yL) context.FillRectangle(DrawingColor.FromArgb(15, 57, 211, 168), new Rectangle(0, yH, chartW, yL - yH));
            }

            var penGF   = new RenderPen(GammaFlipColor,        LineWidth + 1);
            var penVT   = new RenderPen(VolTriggerColor,       LineWidth);
            var penCW   = new RenderPen(CallWallColor,         LineWidth);
            var penPW   = new RenderPen(PutWallColor,          LineWidth);
            var penRP   = new RenderPen(RiskPivotColor,        LineWidth);
            var penVF   = new RenderPen(VannaFlipColor,        1);
            var penCM   = new RenderPen(CharmMagnetColor,      1);
            var penMP   = new RenderPen(MaxPainColor,          LineWidth);
            var penEMH  = new RenderPen(ExpectedMoveHighColor, 1);
            var penEML  = new RenderPen(ExpectedMoveLowColor,  1);
            var penOI1  = new RenderPen(TopOI1Color,           1);
            var penOI2  = new RenderPen(TopOI2Color,           1);
            var penOI3  = new RenderPen(TopOI3Color,           1);

            DrawLevel(context, chartW, lv.GammaFlip,        ShowGammaFlip,        GammaFlipColor,        penGF,  10, 5, $"Gamma Flip  {lv.GammaFlip:F0}  [GEX {lv.GexTotal/1e9:+0.000;-0.000}B]");
            DrawLevel(context, chartW, lv.VolTrigger,       ShowVolTrigger,       VolTriggerColor,       penVT,  8,  4, $"Vol Trigger  {lv.VolTrigger:F0}");
            DrawLevel(context, chartW, lv.CallWall,         ShowCallWall,         CallWallColor,         penCW,  8,  4, $"Call Wall  {lv.CallWall:F0}  [GEX {lv.CallWallGex/1e9:+0.000;-0.000}B]");
            DrawLevel(context, chartW, lv.PutWall,          ShowPutWall,          PutWallColor,          penPW,  8,  4, $"Put Wall  {lv.PutWall:F0}  [GEX {lv.PutWallGex/1e9:+0.000;-0.000}B]");
            DrawLevel(context, chartW, lv.RiskPivot,        ShowRiskPivot,        RiskPivotColor,        penRP,  10, 5, $"Risk Pivot  {lv.RiskPivot:F0}");
            DrawLevel(context, chartW, lv.VannaFlip,        ShowVannaFlip,        VannaFlipColor,        penVF,  2,  4, $"Vanna Flip  {lv.VannaFlip:F0}  [VEX {lv.VexTotal/1e8:+0.00;-0.00}]");
            DrawLevel(context, chartW, lv.CharmMagnet,      ShowCharmMagnet,      CharmMagnetColor,      penCM,  2,  4, $"Charm  {lv.CharmMagnet:F0}");
            DrawLevel(context, chartW, lv.MaxPain,          ShowMaxPain,          MaxPainColor,          penMP,  6,  4, $"Max Pain  {lv.MaxPain:F0}");
            DrawLevel(context, chartW, lv.ExpectedMoveHigh, ShowExpectedMoveHigh, ExpectedMoveHighColor, penEMH, 4,  6, $"EM High  {lv.ExpectedMoveHigh:F0}");
            DrawLevel(context, chartW, lv.ExpectedMoveLow,  ShowExpectedMoveLow,  ExpectedMoveLowColor,  penEML, 4,  6, $"EM Low  {lv.ExpectedMoveLow:F0}");
            DrawLevel(context, chartW, lv.TopOI1,           ShowTopOI1,           TopOI1Color,           penOI1, 3,  6, $"OI #1  {lv.TopOI1:F0}  ({lv.TopOI1Vol:N0})");
            DrawLevel(context, chartW, lv.TopOI2,           ShowTopOI2,           TopOI2Color,           penOI2, 3,  6, $"OI #2  {lv.TopOI2:F0}  ({lv.TopOI2Vol:N0})");
            DrawLevel(context, chartW, lv.TopOI3,           ShowTopOI3,           TopOI3Color,           penOI3, 3,  6, $"OI #3  {lv.TopOI3:F0}  ({lv.TopOI3Vol:N0})");
        }

        private void DrawLevel(RenderContext ctx, int chartW, double price, bool show,
                                DrawingColor color, RenderPen pen, int dashLen, int gapLen, string label)
        {
            if (!show || price <= 0) return;
            int y = (int)ChartInfo.GetYByPrice((decimal)price, false);
            if (y < 0 || y > ChartArea.Height + 200) return;
            int x = 0; bool drawing = true;
            while (x < chartW) { int end = Math.Min(x + (drawing ? dashLen : gapLen), chartW); if (drawing) ctx.DrawLine(pen, x, y, end, y); x = end; drawing = !drawing; }
            var ts = ctx.MeasureString(label, _font);
            int lx = 6, ly = y - (int)ts.Height - 6, lw = (int)ts.Width + 12, lh = (int)ts.Height + 4;
            ctx.FillRectangle(DrawingColor.FromArgb(160, 10, 10, 10),               new Rectangle(lx-2, ly-1, lw, lh));
            ctx.FillRectangle(DrawingColor.FromArgb(220, color.R, color.G, color.B), new Rectangle(lx-2, ly-1, 3,  lh));
            ctx.DrawString(label, _font, DrawingColor.FromArgb(255, color.R, color.G, color.B), lx+4, ly+2);
        }

        private static System.Windows.Controls.ControlTemplate CreateButtonTemplate()
        {
            var t  = new System.Windows.Controls.ControlTemplate(typeof(Button));
            var b  = new System.Windows.FrameworkElementFactory(typeof(Border));
            b.SetBinding(Border.BackgroundProperty,    new System.Windows.Data.Binding("Background")    { RelativeSource = System.Windows.Data.RelativeSource.TemplatedParent });
            b.SetBinding(Border.BorderBrushProperty,   new System.Windows.Data.Binding("BorderBrush")   { RelativeSource = System.Windows.Data.RelativeSource.TemplatedParent });
            b.SetBinding(Border.BorderThicknessProperty,new System.Windows.Data.Binding("BorderThickness"){ RelativeSource = System.Windows.Data.RelativeSource.TemplatedParent });
            b.SetValue(Border.CornerRadiusProperty, new CornerRadius(3));
            var cp = new System.Windows.FrameworkElementFactory(typeof(ContentPresenter));
            cp.SetValue(ContentPresenter.HorizontalAlignmentProperty, HorizontalAlignment.Center);
            cp.SetValue(ContentPresenter.VerticalAlignmentProperty,   VerticalAlignment.Center);
            b.AppendChild(cp); t.VisualTree = b; return t;
        }

        public override void Dispose()
        {
            try { Application.Current?.Dispatcher?.Invoke(() => ClosePanel()); } catch { }
            base.Dispose();
        }

        // ── LoadLevels ────────────────────────────────────────────────────────

        private void LoadLevels()
        {
            if (!File.Exists(JsonPath)) return;
            try
            {
                string json = File.ReadAllText(JsonPath);

                double spot = ParseDouble(json, "spot_es");
                if (spot <= 0) spot = ParseDouble(json, "spot");

                double emHigh = ParseDouble(json, "range_haut_es");
                double emLow  = ParseDouble(json, "range_bas_es");
                double emPts  = ParseDouble(json, "expected_move_es");

                // Top OI strikes — parser le tableau JSON
                double oi1 = 0, oi2 = 0, oi3 = 0;
                long   v1  = 0, v2  = 0, v3  = 0;
                ParseTopOIStrikes(json, out oi1, out v1, out oi2, out v2, out oi3, out v3);

                var snap = new GexSnapshot(
                    gammaFlip:   ParseDouble(json, "gamma_flip"),
                    volTrigger:  ParseDouble(json, "vol_trigger"),
                    callWall:    ParseDouble(json, "call_wall"),
                    putWall:     ParseDouble(json, "put_wall"),
                    riskPivot:   ParseDouble(json, "risk_pivot"),
                    vannaFlip:   ParseDouble(json, "vanna_flip"),
                    charmMagnet: ParseDouble(json, "charm_magnet"),
                    maxPain:     ParseDouble(json, "max_pain_es"),
                    emHigh:      emHigh,
                    emLow:       emLow,
                    emPts:       emPts,
                    topOI1:      oi1, topOI2: oi2, topOI3: oi3,
                    topOI1Vol:   v1,  topOI2Vol: v2, topOI3Vol: v3,
                    pcr:         ParseDouble(json, "pcr"),
                    callWallGex: ParseDouble(json, "call_wall_gex"),
                    putWallGex:  ParseDouble(json, "put_wall_gex"),
                    gexTotal:    ParseDouble(json, "total_gex"),
                    vexTotal:    ParseDouble(json, "total_vex"),
                    cexTotal:    ParseDouble(json, "total_cex"),
                    dexTotal:    ParseDouble(json, "total_dex"),
                    spotLoaded:  spot,
                    gexRegime:   (int)ParseDouble(json, "gex_regime"),
                    vexRegime:   (int)ParseDouble(json, "vex_regime"),
                    tradeDate:   ParseString(json, "trade_date"),
                    loaded:      true
                );
                _levels = snap; _loadedDate = DateTime.Today.ToString("yyyy-MM-dd"); _lastLoadTime = DateTime.Now; _levelsLoaded = true;
            }
            catch (Exception) { _levelsLoaded = false; }
        }

        private void ParseTopOIStrikes(string json,
            out double s1, out long v1, out double s2, out long v2, out double s3, out long v3)
        {
            s1 = s2 = s3 = 0; v1 = v2 = v3 = 0;
            // Trouver le tableau top_oi_strikes
            int arrStart = json.IndexOf("\"top_oi_strikes\"", StringComparison.Ordinal);
            if (arrStart < 0) return;
            int bracket = json.IndexOf('[', arrStart);
            if (bracket < 0) return;
            int end = json.IndexOf(']', bracket);
            if (end < 0) return;
            string arr = json.Substring(bracket, end - bracket + 1);

            // Extraire les 3 premiers objets {…}
            double[] strikes = new double[3]; long[] vols = new long[3]; int found = 0;
            int pos = 0;
            while (found < 3)
            {
                int ob = arr.IndexOf('{', pos); if (ob < 0) break;
                int cb = arr.IndexOf('}', ob);  if (cb < 0) break;
                string obj = arr.Substring(ob, cb - ob + 1);
                double sNq  = ParseDoubleInStr(obj, "strike_es");
                double totOI= ParseDoubleInStr(obj, "total_oi");
                if (sNq > 0) { strikes[found] = sNq; vols[found] = (long)totOI; found++; }
                pos = cb + 1;
            }
            if (found > 0) { s1 = strikes[0]; v1 = vols[0]; }
            if (found > 1) { s2 = strikes[1]; v2 = vols[1]; }
            if (found > 2) { s3 = strikes[2]; v3 = vols[2]; }
        }

        private double ParseDoubleInStr(string s, string key)
        {
            int pos = s.IndexOf("\"" + key + "\"", StringComparison.Ordinal); if (pos < 0) return 0;
            int colon = s.IndexOf(':', pos); if (colon < 0) return 0;
            int start = colon + 1;
            while (start < s.Length && (s[start]==' '||s[start]=='\t')) start++;
            int end = start;
            while (end < s.Length && (char.IsDigit(s[end])||s[end]=='.'||s[end]=='-'||s[end]=='e'||s[end]=='E'||s[end]=='+')) end++;
            if (end == start) return 0;
            return double.TryParse(s.Substring(start, end-start), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double v) ? v : 0;
        }

        private double ParseDouble(string json, string key)
        {
            int pos = json.IndexOf("\"" + key + "\"", StringComparison.Ordinal); if (pos < 0) return 0;
            int colon = json.IndexOf(':', pos); if (colon < 0) return 0;
            int start = colon + 1;
            while (start < json.Length && (json[start]==' '||json[start]=='\t')) start++;
            int end = start;
            while (end < json.Length && (char.IsDigit(json[end])||json[end]=='.'||json[end]=='-'||json[end]=='e'||json[end]=='E'||json[end]=='+')) end++;
            if (end == start) return 0;
            return double.TryParse(json.Substring(start, end-start), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double v) ? v : 0;
        }

        private string ParseString(string json, string key)
        {
            int pos = json.IndexOf("\"" + key + "\"", StringComparison.Ordinal); if (pos < 0) return "";
            int colon = json.IndexOf(':', pos); if (colon < 0) return "";
            int q1 = json.IndexOf('"', colon+1); if (q1 < 0) return "";
            int q2 = json.IndexOf('"', q1+1);    if (q2 < 0) return "";
            return json.Substring(q1+1, q2-q1-1);
        }

        public override string ToString() => "OFK ES GEX Levels";
    }
}
