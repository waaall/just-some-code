using System;
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
    public partial class StatControl : UserControl
    {
        public StatControl()
        {
            InitializeComponent();
            DataBinding("人员信息表");
        }

        // 初始化access database
        static readonly string strCon = @"Driver={Microsoft Access Driver (*.mdb, *.accdb)};Dbq=C:\sysappDatabase\Question.accdb;";
        private readonly OdbcConnection con = new OdbcConnection(strCon);
        private string CurrentTableName = "人员信息表";

        private void StatControl_Load(object sender, EventArgs e)
        {

        }

        private DataTable DataBinding(string tablename)
        {
            con.Open();
            string strSql = $"select * from {tablename}";
            OdbcDataAdapter dadapter = new OdbcDataAdapter();
            dadapter.SelectCommand = new OdbcCommand(strSql, con);
            DataTable table = new DataTable();
            dadapter.Fill(table);
            con.Close();
            dataGridView1.DataSource = table;
            return table;
        }

        private void UpdateData(string tablename)
        {
            dataGridView1.EndEdit();
            string sql = $"select * from {tablename}";
            OdbcDataAdapter da = new OdbcDataAdapter(sql, con);
            OdbcCommandBuilder bld = new OdbcCommandBuilder(da);
            da.UpdateCommand = bld.GetUpdateCommand();
       
            //把DataGridView赋值给dataTbale。(DataTable)的意思是类型转换
            DataTable dt = (DataTable)dataGridView1.DataSource;
            da.Update(dt);
            dt.AcceptChanges();
       
            con.Close();
        }

        private void SetCurrentTable(string TableName)
        {
            CurrentTableName = TableName;
        }

        private void ButTableInfo_Click(object sender, EventArgs e)
        {
            string name = "人员信息表";
            DataBinding(name);
            SetCurrentTable(name);
        }

        private void ButTableA_Click(object sender, EventArgs e)
        {
            string name = "作答表";
            DataBinding(name);
            SetCurrentTable(name);
        }

        private void dataGridView1_CellContentClick(object sender, DataGridViewCellEventArgs e)
        {

        }

        private void StatTip_Popup(object sender, PopupEventArgs e)
        {

        }

        private void ButShare_Click(object sender, EventArgs e)
        {

        }

        private void ButSave_Click(object sender, EventArgs e)
        {

            //UpdateData(CurrentTableName);
            UpdateData("人员信息表");
        }

        private void ButSearch_Click(object sender, EventArgs e)
        {

        }
    }
}
