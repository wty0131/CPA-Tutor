import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import { Layout, Menu } from "antd";
import {
  DashboardOutlined,
  CloseCircleOutlined,
  ApartmentOutlined,
  SettingOutlined,
  TrophyOutlined,
} from "@ant-design/icons";
import Dashboard from "./pages/Dashboard";
import SubjectDetail from "./pages/SubjectDetail";
import Practice from "./pages/Practice";
import WrongBook from "./pages/WrongBook";
import KnowledgeTree from "./pages/KnowledgeTree";
import Admin from "./pages/Admin";
import Exam from "./pages/Exam";

const { Header, Content } = Layout;

const menuItems = [
  { key: "/", icon: <DashboardOutlined />, label: <Link to="/">首页</Link> },
  { key: "/exam", icon: <TrophyOutlined />, label: <Link to="/exam">模拟考</Link> },
  { key: "/wrongbook", icon: <CloseCircleOutlined />, label: <Link to="/wrongbook">错题本</Link> },
  { key: "/knowledge", icon: <ApartmentOutlined />, label: <Link to="/knowledge">知识点</Link> },
  { key: "/admin", icon: <SettingOutlined />, label: <Link to="/admin">管理</Link> },
];

function AppLayout() {
  const location = useLocation();

  const getSelectedKey = () => {
    const path = location.pathname;
    if (path === "/") return "/";
    if (path.startsWith("/exam")) return "/exam";
    if (path.startsWith("/wrongbook")) return "/wrongbook";
    if (path.startsWith("/knowledge")) return "/knowledge";
    if (path.startsWith("/admin")) return "/admin";
    return "/";
  };

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Header style={{ display: "flex", alignItems: "center", padding: "0 24px" }}>
        <div style={{ color: "#fff", fontSize: 20, fontWeight: "bold", marginRight: 40, whiteSpace: "nowrap" }}>
          CPA Tutor
        </div>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[getSelectedKey()]}
          items={menuItems}
          style={{ flex: 1 }}
        />
      </Header>
      <Content style={{ background: "#f5f5f5" }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/subject/:id" element={<SubjectDetail />} />
          <Route path="/practice/:subjectId" element={<Practice />} />
          <Route path="/wrongbook" element={<WrongBook />} />
          <Route path="/knowledge/:subjectId?" element={<KnowledgeTree />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="/exam" element={<Exam />} />
        </Routes>
      </Content>
    </Layout>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  );
}
