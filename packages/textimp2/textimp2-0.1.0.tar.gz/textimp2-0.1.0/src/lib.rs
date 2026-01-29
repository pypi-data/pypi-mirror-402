use arrow::array::{
    BooleanBuilder, Int32Builder, Int64Builder, StringBuilder, TimestampNanosecondBuilder,
};
use arrow::datatypes::{DataType, Field, Schema, TimeUnit};
use arrow::record_batch::RecordBatch;
use imessage_database::tables::table::Table;
use imessage_database::util::dirs::default_db_path;
use pyo3::prelude::*;
use pyo3_arrow::PyRecordBatch;
use rusqlite::Connection;
use std::sync::Arc;

#[pyfunction]
#[pyo3(signature = (path=None))]
fn read_messages(path: Option<String>) -> PyResult<PyRecordBatch> {
    let db_path = path.unwrap_or_else(|| default_db_path().to_string_lossy().to_string());
    let conn = Connection::open(db_path)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    let mut rowid_builder = Int32Builder::new();
    let mut guid_builder = StringBuilder::new();
    let mut text_builder = StringBuilder::new();
    let mut service_builder = StringBuilder::new();
    let mut handle_id_builder = Int32Builder::new();
    let mut destination_caller_id_builder = StringBuilder::new();
    let mut subject_builder = StringBuilder::new();
    let mut date_builder = TimestampNanosecondBuilder::new();
    let mut date_read_builder = TimestampNanosecondBuilder::new();
    let mut date_delivered_builder = TimestampNanosecondBuilder::new();
    let mut is_from_me_builder = BooleanBuilder::new();
    let mut is_read_builder = BooleanBuilder::new();
    let mut item_type_builder = Int32Builder::new();
    let mut other_handle_builder = Int32Builder::new();
    let mut share_status_builder = BooleanBuilder::new();
    let mut share_direction_builder = BooleanBuilder::new();
    let mut group_title_builder = StringBuilder::new();
    let mut group_action_type_builder = Int32Builder::new();
    let mut associated_message_guid_builder = StringBuilder::new();
    let mut associated_message_type_builder = Int32Builder::new();
    let mut balloon_bundle_id_builder = StringBuilder::new();
    let mut expressive_send_style_id_builder = StringBuilder::new();
    let mut thread_originator_guid_builder = StringBuilder::new();
    let mut thread_originator_part_builder = StringBuilder::new();
    let mut date_edited_builder = TimestampNanosecondBuilder::new();
    let mut associated_message_emoji_builder = StringBuilder::new();
    let mut chat_id_builder = Int32Builder::new();
    let mut num_attachments_builder = Int32Builder::new();
    let mut deleted_from_builder = Int32Builder::new();
    let mut num_replies_builder = Int32Builder::new();
    // Complex types stringified
    let mut components_builder = StringBuilder::new();
    let mut edited_parts_builder = StringBuilder::new();

    let mac_epoch_offset = 978307200_000_000_000i64;

    imessage_database::tables::messages::Message::stream(&conn, |msg_result| {
        let msg = msg_result.map_err(|e| imessage_database::error::table::TableError::from(e))?;

        rowid_builder.append_value(msg.rowid);
        guid_builder.append_value(&msg.guid);

        if let Some(t) = &msg.text {
            text_builder.append_value(t);
        } else {
            text_builder.append_null();
        }
        if let Some(s) = &msg.service {
            service_builder.append_value(s);
        } else {
            service_builder.append_null();
        }
        if let Some(h) = msg.handle_id {
            handle_id_builder.append_value(h);
        } else {
            handle_id_builder.append_null();
        }
        if let Some(d) = &msg.destination_caller_id {
            destination_caller_id_builder.append_value(d);
        } else {
            destination_caller_id_builder.append_null();
        }
        if let Some(s) = &msg.subject {
            subject_builder.append_value(s);
        } else {
            subject_builder.append_null();
        }

        date_builder.append_value(msg.date + mac_epoch_offset);
        date_read_builder.append_value(msg.date_read + mac_epoch_offset);
        date_delivered_builder.append_value(msg.date_delivered + mac_epoch_offset);

        is_from_me_builder.append_value(msg.is_from_me);
        is_read_builder.append_value(msg.is_read);
        item_type_builder.append_value(msg.item_type);

        if let Some(o) = msg.other_handle {
            other_handle_builder.append_value(o);
        } else {
            other_handle_builder.append_null();
        }

        share_status_builder.append_value(msg.share_status);
        if let Some(s) = msg.share_direction {
            share_direction_builder.append_value(s);
        } else {
            share_direction_builder.append_null();
        }

        if let Some(g) = &msg.group_title {
            group_title_builder.append_value(g);
        } else {
            group_title_builder.append_null();
        }
        group_action_type_builder.append_value(msg.group_action_type);

        if let Some(a) = &msg.associated_message_guid {
            associated_message_guid_builder.append_value(a);
        } else {
            associated_message_guid_builder.append_null();
        }
        if let Some(a) = msg.associated_message_type {
            associated_message_type_builder.append_value(a);
        } else {
            associated_message_type_builder.append_null();
        }
        if let Some(b) = &msg.balloon_bundle_id {
            balloon_bundle_id_builder.append_value(b);
        } else {
            balloon_bundle_id_builder.append_null();
        }
        if let Some(e) = &msg.expressive_send_style_id {
            expressive_send_style_id_builder.append_value(e);
        } else {
            expressive_send_style_id_builder.append_null();
        }
        if let Some(t) = &msg.thread_originator_guid {
            thread_originator_guid_builder.append_value(t);
        } else {
            thread_originator_guid_builder.append_null();
        }
        if let Some(t) = &msg.thread_originator_part {
            thread_originator_part_builder.append_value(t);
        } else {
            thread_originator_part_builder.append_null();
        }

        date_edited_builder.append_value(msg.date_edited + mac_epoch_offset);

        if let Some(a) = &msg.associated_message_emoji {
            associated_message_emoji_builder.append_value(a);
        } else {
            associated_message_emoji_builder.append_null();
        }
        if let Some(c) = msg.chat_id {
            chat_id_builder.append_value(c);
        } else {
            chat_id_builder.append_null();
        }

        num_attachments_builder.append_value(msg.num_attachments);
        if let Some(d) = msg.deleted_from {
            deleted_from_builder.append_value(d);
        } else {
            deleted_from_builder.append_null();
        }
        num_replies_builder.append_value(msg.num_replies);

        components_builder.append_value(format!("{:?}", msg.components));
        if let Some(e) = &msg.edited_parts {
            edited_parts_builder.append_value(format!("{:?}", e));
        } else {
            edited_parts_builder.append_null();
        }

        Ok::<(), imessage_database::error::table::TableError>(())
    })
    .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    let schema = Schema::new(vec![
        Field::new("rowid", DataType::Int32, false),
        Field::new("guid", DataType::Utf8, false),
        Field::new("text", DataType::Utf8, true),
        Field::new("service", DataType::Utf8, true),
        Field::new("handle_id", DataType::Int32, true),
        Field::new("destination_caller_id", DataType::Utf8, true),
        Field::new("subject", DataType::Utf8, true),
        Field::new(
            "date",
            DataType::Timestamp(TimeUnit::Nanosecond, None),
            false,
        ),
        Field::new(
            "date_read",
            DataType::Timestamp(TimeUnit::Nanosecond, None),
            false,
        ),
        Field::new(
            "date_delivered",
            DataType::Timestamp(TimeUnit::Nanosecond, None),
            false,
        ),
        Field::new("is_from_me", DataType::Boolean, false),
        Field::new("is_read", DataType::Boolean, false),
        Field::new("item_type", DataType::Int32, false),
        Field::new("other_handle", DataType::Int32, true),
        Field::new("share_status", DataType::Boolean, false),
        Field::new("share_direction", DataType::Boolean, true),
        Field::new("group_title", DataType::Utf8, true),
        Field::new("group_action_type", DataType::Int32, false),
        Field::new("associated_message_guid", DataType::Utf8, true),
        Field::new("associated_message_type", DataType::Int32, true),
        Field::new("balloon_bundle_id", DataType::Utf8, true),
        Field::new("expressive_send_style_id", DataType::Utf8, true),
        Field::new("thread_originator_guid", DataType::Utf8, true),
        Field::new("thread_originator_part", DataType::Utf8, true),
        Field::new(
            "date_edited",
            DataType::Timestamp(TimeUnit::Nanosecond, None),
            false,
        ),
        Field::new("associated_message_emoji", DataType::Utf8, true),
        Field::new("chat_id", DataType::Int32, true),
        Field::new("num_attachments", DataType::Int32, false),
        Field::new("deleted_from", DataType::Int32, true),
        Field::new("num_replies", DataType::Int32, false),
        Field::new("components_debug", DataType::Utf8, false),
        Field::new("edited_parts_debug", DataType::Utf8, true),
    ]);

    let batch = RecordBatch::try_new(
        Arc::new(schema),
        vec![
            Arc::new(rowid_builder.finish()),
            Arc::new(guid_builder.finish()),
            Arc::new(text_builder.finish()),
            Arc::new(service_builder.finish()),
            Arc::new(handle_id_builder.finish()),
            Arc::new(destination_caller_id_builder.finish()),
            Arc::new(subject_builder.finish()),
            Arc::new(date_builder.finish()),
            Arc::new(date_read_builder.finish()),
            Arc::new(date_delivered_builder.finish()),
            Arc::new(is_from_me_builder.finish()),
            Arc::new(is_read_builder.finish()),
            Arc::new(item_type_builder.finish()),
            Arc::new(other_handle_builder.finish()),
            Arc::new(share_status_builder.finish()),
            Arc::new(share_direction_builder.finish()),
            Arc::new(group_title_builder.finish()),
            Arc::new(group_action_type_builder.finish()),
            Arc::new(associated_message_guid_builder.finish()),
            Arc::new(associated_message_type_builder.finish()),
            Arc::new(balloon_bundle_id_builder.finish()),
            Arc::new(expressive_send_style_id_builder.finish()),
            Arc::new(thread_originator_guid_builder.finish()),
            Arc::new(thread_originator_part_builder.finish()),
            Arc::new(date_edited_builder.finish()),
            Arc::new(associated_message_emoji_builder.finish()),
            Arc::new(chat_id_builder.finish()),
            Arc::new(num_attachments_builder.finish()),
            Arc::new(deleted_from_builder.finish()),
            Arc::new(num_replies_builder.finish()),
            Arc::new(components_builder.finish()),
            Arc::new(edited_parts_builder.finish()),
        ],
    )
    .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    Ok(PyRecordBatch::new(batch))
}

#[pyfunction]
#[pyo3(signature = (path=None))]
fn read_handles(path: Option<String>) -> PyResult<PyRecordBatch> {
    let db_path = path.unwrap_or_else(|| default_db_path().to_string_lossy().to_string());
    let conn = Connection::open(db_path)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    let mut rowid_builder = Int64Builder::new();
    let mut id_builder = StringBuilder::new();
    // person_centric_id seems to be available likely as string
    let mut person_centric_id_builder = StringBuilder::new();

    imessage_database::tables::handle::Handle::stream(&conn, |handle_result| {
        let handle =
            handle_result.map_err(|e| imessage_database::error::table::TableError::from(e))?;

        rowid_builder.append_value(handle.rowid as i64);
        id_builder.append_value(&handle.id);

        if let Some(pid) = &handle.person_centric_id {
            person_centric_id_builder.append_value(pid);
        } else {
            person_centric_id_builder.append_null();
        }
        Ok::<(), imessage_database::error::table::TableError>(())
    })
    .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    let schema = Schema::new(vec![
        Field::new("rowid", DataType::Int64, false),
        Field::new("id", DataType::Utf8, false),
        Field::new("person_centric_id", DataType::Utf8, true),
    ]);

    let batch = RecordBatch::try_new(
        Arc::new(schema),
        vec![
            Arc::new(rowid_builder.finish()),
            Arc::new(id_builder.finish()),
            Arc::new(person_centric_id_builder.finish()),
        ],
    )
    .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    Ok(PyRecordBatch::new(batch))
}

#[pyfunction]
#[pyo3(signature = (path=None))]
fn read_attachments(path: Option<String>) -> PyResult<PyRecordBatch> {
    let db_path = path.unwrap_or_else(|| default_db_path().to_string_lossy().to_string());
    let conn = Connection::open(db_path)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    let mut rowid_builder = Int32Builder::new();
    let mut guid_builder = StringBuilder::new();
    let mut created_date_builder = TimestampNanosecondBuilder::new();
    let mut start_date_builder = TimestampNanosecondBuilder::new();
    let mut filename_builder = StringBuilder::new();
    let mut uti_builder = StringBuilder::new();
    let mut mime_type_builder = StringBuilder::new();
    let mut transfer_state_builder = Int32Builder::new();
    let mut is_outgoing_builder = BooleanBuilder::new();
    let mut user_info_builder = StringBuilder::new();
    let mut transfer_name_builder = StringBuilder::new();
    let mut total_bytes_builder = Int64Builder::new();
    let mut is_sticker_builder = BooleanBuilder::new();
    let mut sticker_user_info_builder = StringBuilder::new();
    let mut attribution_info_builder = StringBuilder::new();
    let mut hide_attachment_builder = BooleanBuilder::new();
    let mut original_guid_builder = StringBuilder::new();

    let mac_epoch_offset = 978307200_000_000_000i64;

    let mut stmt = conn
        .prepare(
            "SELECT 
                ROWID, 
                guid, 
                created_date, 
                start_date, 
                filename, 
                uti, 
                mime_type, 
                transfer_state, 
                is_outgoing, 
                user_info, 
                transfer_name, 
                total_bytes, 
                is_sticker, 
                sticker_user_info, 
                attribution_info, 
                hide_attachment, 
                original_guid 
            FROM attachment",
        )
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    let rows = stmt
        .query_map([], |row| {
            Ok((
                row.get::<_, i32>(0)?,
                row.get::<_, String>(1)?,
                row.get::<_, i64>(2)?,
                row.get::<_, i64>(3)?,
                row.get::<_, Option<String>>(4)?,
                row.get::<_, Option<String>>(5)?,
                row.get::<_, Option<String>>(6)?,
                row.get::<_, Option<i32>>(7)?,
                row.get::<_, Option<i32>>(8)?,
                row.get::<_, Option<Vec<u8>>>(9)?,
                row.get::<_, Option<String>>(10)?,
                row.get::<_, Option<i64>>(11)?,
                row.get::<_, Option<i32>>(12)?,
                row.get::<_, Option<Vec<u8>>>(13)?,
                row.get::<_, Option<Vec<u8>>>(14)?,
                row.get::<_, Option<i32>>(15)?,
                row.get::<_, Option<String>>(16)?,
            ))
        })
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    for row_result in rows {
        let (
            rowid,
            guid,
            created_date,
            start_date,
            filename,
            uti,
            mime_type,
            transfer_state,
            is_outgoing,
            user_info,
            transfer_name,
            total_bytes,
            is_sticker,
            sticker_user_info,
            attribution_info,
            hide_attachment,
            original_guid,
        ) = row_result
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        rowid_builder.append_value(rowid);
        guid_builder.append_value(guid);
        created_date_builder.append_value(created_date + mac_epoch_offset);
        start_date_builder.append_value(start_date + mac_epoch_offset);

        if let Some(f) = filename {
            filename_builder.append_value(f);
        } else {
            filename_builder.append_null();
        }

        if let Some(u) = uti {
            uti_builder.append_value(u);
        } else {
            uti_builder.append_null();
        }

        if let Some(m) = mime_type {
            mime_type_builder.append_value(m);
        } else {
            mime_type_builder.append_null();
        }

        if let Some(t) = transfer_state {
            transfer_state_builder.append_value(t);
        } else {
            transfer_state_builder.append_null();
        }

        if let Some(i) = is_outgoing {
            is_outgoing_builder.append_value(i != 0);
        } else {
            is_outgoing_builder.append_null();
        }

        if let Some(u) = user_info {
            user_info_builder.append_value(format!("{:?}", u));
        } else {
            user_info_builder.append_null();
        }

        if let Some(t) = transfer_name {
            transfer_name_builder.append_value(t);
        } else {
            transfer_name_builder.append_null();
        }

        if let Some(t) = total_bytes {
            total_bytes_builder.append_value(t);
        } else {
            total_bytes_builder.append_null();
        }

        if let Some(i) = is_sticker {
            is_sticker_builder.append_value(i != 0);
        } else {
            is_sticker_builder.append_null();
        }

        if let Some(s) = sticker_user_info {
            sticker_user_info_builder.append_value(format!("{:?}", s));
        } else {
            sticker_user_info_builder.append_null();
        }

        if let Some(a) = attribution_info {
            attribution_info_builder.append_value(format!("{:?}", a));
        } else {
            attribution_info_builder.append_null();
        }

        if let Some(h) = hide_attachment {
            hide_attachment_builder.append_value(h != 0);
        } else {
            hide_attachment_builder.append_null();
        }

        if let Some(o) = original_guid {
            original_guid_builder.append_value(o);
        } else {
            original_guid_builder.append_null();
        }
    }

    let schema = Schema::new(vec![
        Field::new("rowid", DataType::Int32, false),
        Field::new("guid", DataType::Utf8, false),
        Field::new(
            "created_date",
            DataType::Timestamp(TimeUnit::Nanosecond, None),
            false,
        ),
        Field::new(
            "start_date",
            DataType::Timestamp(TimeUnit::Nanosecond, None),
            false,
        ),
        Field::new("filename", DataType::Utf8, true),
        Field::new("uti", DataType::Utf8, true),
        Field::new("mime_type", DataType::Utf8, true),
        Field::new("transfer_state", DataType::Int32, true),
        Field::new("is_outgoing", DataType::Boolean, true),
        Field::new("user_info_debug", DataType::Utf8, true),
        Field::new("transfer_name", DataType::Utf8, true),
        Field::new("total_bytes", DataType::Int64, true),
        Field::new("is_sticker", DataType::Boolean, true),
        Field::new("sticker_user_info_debug", DataType::Utf8, true),
        Field::new("attribution_info_debug", DataType::Utf8, true),
        Field::new("hide_attachment", DataType::Boolean, true),
        Field::new("original_guid", DataType::Utf8, true),
    ]);

    let batch = RecordBatch::try_new(
        Arc::new(schema),
        vec![
            Arc::new(rowid_builder.finish()),
            Arc::new(guid_builder.finish()),
            Arc::new(created_date_builder.finish()),
            Arc::new(start_date_builder.finish()),
            Arc::new(filename_builder.finish()),
            Arc::new(uti_builder.finish()),
            Arc::new(mime_type_builder.finish()),
            Arc::new(transfer_state_builder.finish()),
            Arc::new(is_outgoing_builder.finish()),
            Arc::new(user_info_builder.finish()),
            Arc::new(transfer_name_builder.finish()),
            Arc::new(total_bytes_builder.finish()),
            Arc::new(is_sticker_builder.finish()),
            Arc::new(sticker_user_info_builder.finish()),
            Arc::new(attribution_info_builder.finish()),
            Arc::new(hide_attachment_builder.finish()),
            Arc::new(original_guid_builder.finish()),
        ],
    )
    .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    Ok(PyRecordBatch::new(batch))
}

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(read_messages, m)?)?;
    m.add_function(wrap_pyfunction!(read_handles, m)?)?;
    m.add_function(wrap_pyfunction!(read_attachments, m)?)?;
    Ok(())
}
