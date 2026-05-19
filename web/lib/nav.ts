export type NavItem = {
  href: string;
  label: string;
  soon?: boolean;
};

export type NavGroup = {
  label: string;
  items: NavItem[];
};

export const NAV_GROUPS: NavGroup[] = [
  {
    label: "Calculate",
    items: [
      { href: "/name", label: "Name" },
      { href: "/phone", label: "Phone" },
    ],
  },
];
