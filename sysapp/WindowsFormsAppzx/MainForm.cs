using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace WindowsFormsAppzx
{
    public partial class MainForm : Form
    {
        public MainForm()
        {
            InitializeComponent();
        }

        // 声明public control的对象。
        public StatControl stat;
        public AnswerControl Answer;


        private void MainForm_Load(object sender, EventArgs e)
        {
            Answer = new AnswerControl();
        }

        private void ButStat_Click(object sender, EventArgs e)
        {
            // 这是用form形式的子窗口
            //StatForm Stform = new StatForm();
            //Stform.MdiParent = this;
            //Stform.Parent = this.MainPanel;
            //Stform.Show();
            stat = new StatControl();
            stat.Show();
            MainPanel.Controls.Clear();    //清空原容器上的控件
            MainPanel.Controls.Add(stat);    //将窗体三加入容器panel

        }

        private void ButAnswer_Click(object sender, EventArgs e)
        {
            Answer.Show();
            MainPanel.Controls.Clear();    //清空原容器上的控件
            MainPanel.Controls.Add(Answer);    //将窗体三加入容器panel
        }

        private void ButEdit_Click(object sender, EventArgs e)
        {

        }

        private void ButSet_Click(object sender, EventArgs e)
        {

        }

        private void ButUser_Click(object sender, EventArgs e)
        {

        }

        private void MainTip_Popup(object sender, PopupEventArgs e)
        {

        }


    }
}
