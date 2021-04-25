
namespace WindowsFormsAppzx
{
    partial class StatControl
    {
        /// <summary> 
        /// 必需的设计器变量。
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary> 
        /// 清理所有正在使用的资源。
        /// </summary>
        /// <param name="disposing">如果应释放托管资源，为 true；否则为 false。</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region 组件设计器生成的代码

        /// <summary> 
        /// 设计器支持所需的方法 - 不要修改
        /// 使用代码编辑器修改此方法的内容。
        /// </summary>
        private void InitializeComponent()
        {
            this.components = new System.ComponentModel.Container();
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(StatControl));
            this.ButTableInfo = new System.Windows.Forms.Button();
            this.ButTableA = new System.Windows.Forms.Button();
            this.dataGridView1 = new System.Windows.Forms.DataGridView();
            this.flowLayoutPanel1 = new System.Windows.Forms.FlowLayoutPanel();
            this.ButSave = new System.Windows.Forms.Button();
            this.SearchBox = new System.Windows.Forms.TextBox();
            this.ButSearch = new System.Windows.Forms.Button();
            this.ButShare = new System.Windows.Forms.Button();
            this.StatTip = new System.Windows.Forms.ToolTip(this.components);
            ((System.ComponentModel.ISupportInitialize)(this.dataGridView1)).BeginInit();
            this.flowLayoutPanel1.SuspendLayout();
            this.SuspendLayout();
            // 
            // ButTableInfo
            // 
            this.ButTableInfo.Location = new System.Drawing.Point(929, 532);
            this.ButTableInfo.Name = "ButTableInfo";
            this.ButTableInfo.Size = new System.Drawing.Size(33, 154);
            this.ButTableInfo.TabIndex = 0;
            this.ButTableInfo.Text = "人员信息表";
            this.ButTableInfo.UseVisualStyleBackColor = true;
            this.ButTableInfo.Click += new System.EventHandler(this.ButTableInfo_Click);
            // 
            // ButTableA
            // 
            this.ButTableA.Location = new System.Drawing.Point(929, 433);
            this.ButTableA.Name = "ButTableA";
            this.ButTableA.Size = new System.Drawing.Size(33, 93);
            this.ButTableA.TabIndex = 1;
            this.ButTableA.Text = "作答表";
            this.ButTableA.UseVisualStyleBackColor = true;
            this.ButTableA.Click += new System.EventHandler(this.ButTableA_Click);
            // 
            // dataGridView1
            // 
            this.dataGridView1.BackgroundColor = System.Drawing.SystemColors.Control;
            this.dataGridView1.ColumnHeadersHeightSizeMode = System.Windows.Forms.DataGridViewColumnHeadersHeightSizeMode.AutoSize;
            this.dataGridView1.Location = new System.Drawing.Point(0, 82);
            this.dataGridView1.Name = "dataGridView1";
            this.dataGridView1.RowHeadersWidth = 62;
            this.dataGridView1.RowTemplate.Height = 32;
            this.dataGridView1.Size = new System.Drawing.Size(929, 604);
            this.dataGridView1.TabIndex = 2;
            this.dataGridView1.CellContentClick += new System.Windows.Forms.DataGridViewCellEventHandler(this.dataGridView1_CellContentClick);
            // 
            // flowLayoutPanel1
            // 
            this.flowLayoutPanel1.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.flowLayoutPanel1.Controls.Add(this.ButSave);
            this.flowLayoutPanel1.Controls.Add(this.SearchBox);
            this.flowLayoutPanel1.Controls.Add(this.ButSearch);
            this.flowLayoutPanel1.Controls.Add(this.ButShare);
            this.flowLayoutPanel1.Location = new System.Drawing.Point(0, 0);
            this.flowLayoutPanel1.Name = "flowLayoutPanel1";
            this.flowLayoutPanel1.Size = new System.Drawing.Size(929, 83);
            this.flowLayoutPanel1.TabIndex = 3;
            // 
            // ButSave
            // 
            this.ButSave.BackgroundImage = ((System.Drawing.Image)(resources.GetObject("ButSave.BackgroundImage")));
            this.ButSave.BackgroundImageLayout = System.Windows.Forms.ImageLayout.Zoom;
            this.ButSave.FlatAppearance.BorderSize = 0;
            this.ButSave.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.ButSave.Location = new System.Drawing.Point(27, 21);
            this.ButSave.Margin = new System.Windows.Forms.Padding(27, 21, 27, 21);
            this.ButSave.Name = "ButSave";
            this.ButSave.Size = new System.Drawing.Size(36, 42);
            this.ButSave.TabIndex = 1;
            this.StatTip.SetToolTip(this.ButSave, "保存更改");
            this.ButSave.UseVisualStyleBackColor = true;
            this.ButSave.Click += new System.EventHandler(this.ButSave_Click);
            // 
            // SearchBox
            // 
            this.SearchBox.Location = new System.Drawing.Point(590, 26);
            this.SearchBox.Margin = new System.Windows.Forms.Padding(500, 26, 5, 21);
            this.SearchBox.Name = "SearchBox";
            this.SearchBox.Size = new System.Drawing.Size(137, 31);
            this.SearchBox.TabIndex = 5;
            // 
            // ButSearch
            // 
            this.ButSearch.BackgroundImage = ((System.Drawing.Image)(resources.GetObject("ButSearch.BackgroundImage")));
            this.ButSearch.BackgroundImageLayout = System.Windows.Forms.ImageLayout.Zoom;
            this.ButSearch.FlatAppearance.BorderSize = 0;
            this.ButSearch.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.ButSearch.Location = new System.Drawing.Point(737, 21);
            this.ButSearch.Margin = new System.Windows.Forms.Padding(5, 21, 27, 21);
            this.ButSearch.Name = "ButSearch";
            this.ButSearch.Size = new System.Drawing.Size(36, 42);
            this.ButSearch.TabIndex = 6;
            this.StatTip.SetToolTip(this.ButSearch, "搜索");
            this.ButSearch.UseVisualStyleBackColor = true;
            this.ButSearch.Click += new System.EventHandler(this.ButSearch_Click);
            // 
            // ButShare
            // 
            this.ButShare.BackgroundImage = ((System.Drawing.Image)(resources.GetObject("ButShare.BackgroundImage")));
            this.ButShare.BackgroundImageLayout = System.Windows.Forms.ImageLayout.Zoom;
            this.ButShare.FlatAppearance.BorderSize = 0;
            this.ButShare.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.ButShare.Location = new System.Drawing.Point(864, 21);
            this.ButShare.Margin = new System.Windows.Forms.Padding(64, 21, 18, 21);
            this.ButShare.Name = "ButShare";
            this.ButShare.Size = new System.Drawing.Size(36, 42);
            this.ButShare.TabIndex = 7;
            this.StatTip.SetToolTip(this.ButShare, "导出");
            this.ButShare.UseVisualStyleBackColor = true;
            this.ButShare.Click += new System.EventHandler(this.ButShare_Click);
            // 
            // StatTip
            // 
            this.StatTip.Popup += new System.Windows.Forms.PopupEventHandler(this.StatTip_Popup);
            // 
            // StatControl
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(10F, 25F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.Controls.Add(this.flowLayoutPanel1);
            this.Controls.Add(this.dataGridView1);
            this.Controls.Add(this.ButTableA);
            this.Controls.Add(this.ButTableInfo);
            this.Name = "StatControl";
            this.Size = new System.Drawing.Size(960, 700);
            this.Load += new System.EventHandler(this.StatControl_Load);
            ((System.ComponentModel.ISupportInitialize)(this.dataGridView1)).EndInit();
            this.flowLayoutPanel1.ResumeLayout(false);
            this.flowLayoutPanel1.PerformLayout();
            this.ResumeLayout(false);

        }

        #endregion

        private System.Windows.Forms.Button ButTableInfo;
        private System.Windows.Forms.Button ButTableA;
        private System.Windows.Forms.DataGridView dataGridView1;
        private System.Windows.Forms.FlowLayoutPanel flowLayoutPanel1;
        private System.Windows.Forms.ToolTip StatTip;
        private System.Windows.Forms.TextBox SearchBox;
        private System.Windows.Forms.Button ButSave;
        private System.Windows.Forms.Button ButSearch;
        private System.Windows.Forms.Button ButShare;
    }
}
