using System;
using System.Web;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Data.Odbc;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace WindowsFormsAppzx
{
    public partial class AnswerControl : UserControl
    {
        public AnswerControl()
        {
            InitializeComponent();
            QuesPanel.Visible = false;
        }

        static string strCon1 = @"Driver={Microsoft Access Driver (*.mdb, *.accdb)};Dbq=C:\sysappDatabase\Question.accdb;";
        private readonly OdbcConnection conn = new OdbcConnection(strCon1);

        private void AddInfoToData()
        {
            conn.Open();
            string columns = "姓名,性别,年龄,身高,体重,职业,学历";
            string strSql = $"insert into 人员信息表 ({columns}) values (?,?,?,?,?,?,?)";
            
            OdbcCommand inscmd = new OdbcCommand(strSql, this.conn);
            
            inscmd.Parameters.AddWithValue("姓名", this.BoxName.Text);
            inscmd.Parameters.AddWithValue("性别", this.BoxGender.Text);
            inscmd.Parameters.AddWithValue("年龄", this.BoxAge.Text);
            inscmd.Parameters.AddWithValue("身高", this.BoxHight.Text);
            inscmd.Parameters.AddWithValue("体重", this.BoxWight.Text);
            inscmd.Parameters.AddWithValue("职业", this.BoxCarrer.Text);
            inscmd.Parameters.AddWithValue("学历", this.BoxEdu.Text);
            inscmd.ExecuteNonQuery();

            conn.Close();
        }

        private void tableLayoutPanel1_Paint(object sender, PaintEventArgs e)
        {

        }

        private void ButNext_Click(object sender, EventArgs e)
        {
            AddInfoToData();
            QuesPanel.Visible = true;
        }

    }
}
