pub mod game;
pub mod player;

pub struct TableMapping {
    pub member_name: String,
    pub gen_func: fn(String, bool) -> String,
    pub where_stmt: String
}

pub trait PostgresJsonHolder {
    fn table_name() -> String;

    fn children() -> Vec<TableMapping>;

    fn generate_sql(filters: String, first: bool) -> String {
        let mut children: Vec<String> = vec![];
        let mut child_str = "".to_string();
        for child in Self::children() {
            children.push(format!("'{}', ({})", child.member_name, (child.gen_func)(child.where_stmt, false)))
        }
        if !children.is_empty() {
            child_str = format!(" || jsonb_build_object({})", children.join(", "));
        }
        format!("SELECT to_jsonb({table}.*){extra}{as_stmt} FROM {table} {filters}", as_stmt=if first { " AS items" } else { "" }, table=Self::table_name(), extra=child_str, filters=filters)
    }
}

#[macro_export]
macro_rules! impl_json {
    ($struct_name: ident) => {
        const _: fn () = || {
            fn assert_impls_trait<T: PostgresJsonHolder>() {}
            assert_impls_trait::<$struct_name>();
        };

        #[derive(sqlx::FromRow)]
        #[allow(dead_code)]
        struct ItemHolder {
            pub items: sqlx::types::Json<$struct_name>,
        }

        #[allow(dead_code)]
        async fn get_items(pool: &sqlx::Pool<sqlx::Postgres>, suffix: &str, binds: sqlx::postgres::PgArguments) -> Result<Vec<$struct_name>, sqlx::Error> {
            let query = $struct_name::generate_sql(suffix.to_string(), true);
            Ok(sqlx::query_as_with::<sqlx::Postgres, ItemHolder, _>(&query, binds)
            .fetch_all(pool)
            .await?.into_iter().map(|item| item.items.0).collect())
        }

        #[allow(dead_code)]
        async fn get_item(pool: &sqlx::Pool<sqlx::Postgres>, suffix: &str, binds: sqlx::postgres::PgArguments) -> Result<$struct_name, sqlx::Error> {
            let query = $struct_name::generate_sql(suffix.to_string(), true);
            Ok(sqlx::query_as_with::<sqlx::Postgres, ItemHolder, _>(&query, binds)
            .fetch_one(pool)
            .await?.items.0)
        }
    }
}